#!/usr/bin/env python
"""
Worker 启动脚本（带错误捕获）
"""
import logging
import sys
import traceback
from pathlib import Path

# 把项目根加入 PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('worker.log', encoding='utf-8')
    ]
)

log = logging.getLogger(__name__)

def main():
    try:
        log.info("正在导入 Worker 配置...")
        from core.worker import WorkerSettings
        from arq import Worker
        import asyncio

        log.info(f"Redis 配置: {WorkerSettings.redis_settings}")
        log.info(f"队列名称: {WorkerSettings.queue_name}")
        log.info(f"任务函数: {[f.__name__ for f in WorkerSettings.functions]}")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        log.info("正在创建 Worker...")
        worker = Worker(
            functions=WorkerSettings.functions,
            redis_settings=WorkerSettings.redis_settings,
            queue_name=WorkerSettings.queue_name,
        )

        log.info("Worker 启动成功，开始运行...")
        loop.run_until_complete(worker.run())

    except Exception as e:
        log.error(f"Worker 启动失败: {e}")
        log.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    main()
