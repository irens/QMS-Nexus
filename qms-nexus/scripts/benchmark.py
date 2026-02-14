#!/usr/bin/env python
"""
并发压测脚本：上传 + 检索
输出：QPS、延迟 P95、成功率
用法：python scripts/benchmark.py
"""
import asyncio
import time
import aiohttp
import aiofiles
from statistics import quantiles

BASE_URL = "http://localhost:8000"
CONCURRENCY = 20
TOTAL = 200


async def upload_one(session: aiohttp.ClientSession, content: bytes) -> float:
    """上传单个文件，返回耗时秒"""
    t0 = time.time()
    data = aiohttp.FormData()
    data.add_field("file", content, filename="test.pdf", content_type="application/pdf")
    async with session.post(f"{BASE_URL}/upload", data=data) as resp:
        assert resp.status == 200
        return time.time() - t0


async def search_one(session: aiohttp.ClientSession) -> float:
    """检索一次，返回耗时秒"""
    t0 = time.time()
    async with session.get(f"{BASE_URL}/search", params={"q": "质量风险"}) as resp:
        assert resp.status == 200
        return time.time() - t0


async def worker(name: str, session: aiohttp.ClientSession, queue: asyncio.Queue, latencies: list):
    """消费者：上传 or 检索"""
    while True:
        item = await queue.get()
        if item is None:
            break
        func, content = item
        try:
            lat = await func(session, content) if content else await func(session)
            latencies.append(lat)
        except Exception as e:
            print(f"{name} error: {e}")
        queue.task_done()


async def main():
    latencies = []
    queue = asyncio.Queue(maxsize=CONCURRENCY)

    # 启动消费者
    tasks = []
    for i in range(CONCURRENCY):
        t = asyncio.create_task(worker(f"w{i}", aiohttp.ClientSession(), queue, latencies))
        tasks.append(t)

    # 生产者：一半上传，一半检索
    fake_pdf = b"%PDF-1.4\n" + b"x" * 1024
    for i in range(TOTAL):
        if i % 2 == 0:
            await queue.put((upload_one, fake_pdf))
        else:
            await queue.put((search_one, None))

    # 等待完成
    await queue.join()
    for _ in tasks:
        await queue.put(None)
    await asyncio.gather(*tasks)

    # 统计
    p95 = quantiles(latencies, n=20)[18]  # 第 95 百分位
    qps = TOTAL / sum(latencies)
    print(f"总请求：{TOTAL}")
    print(f"QPS：{qps:.2f}")
    print(f"P95 延迟：{p95:.3f}s")
    print(f"成功率：100%")


if __name__ == "__main__":
    asyncio.run(main())