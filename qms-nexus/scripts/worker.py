#!/usr/bin/env python
"""
arq Worker 启动入口
用法：python scripts/worker.py
"""
import logging
import sys
from pathlib import Path

# 把项目根加入 PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.worker import WorkerSettings

logging.basicConfig(level=logging.INFO)


def main():
    from arq import Worker
    import asyncio
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    worker = Worker(
        functions=WorkerSettings.functions,
        redis_settings=WorkerSettings.redis_settings,
    )
    loop.run_until_complete(worker.run())


if __name__ == "__main__":
    main()