#!/usr/bin/env python
"""
arq Worker 启动入口（调试版）
用法：python scripts/worker_debug.py
"""
import logging
import sys
import traceback
from pathlib import Path

# 把项目根加入 PYTHONPATH
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger(__name__)

def