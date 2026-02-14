#!/usr/bin/env python
"""
arq Worker 启动入口
用法：python scripts/worker.py
"""
import asyncio
import logging
import sys
from pathlib import Path

# 把项目根加入 PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.worker import WorkerSettings

logging.basicConfig(level=logging.INFO)


async def main():
    from arq import Worker
    await Worker(
        functions=WorkerSettings.functions,
        redis_settings=WorkerSettings.redis_settings,
    ).run()


if __name__ == "__main__":
    asyncio.run(main())