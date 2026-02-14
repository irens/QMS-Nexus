"""
统一 JSON 日志格式：时间戳、用户、耗时、级别、消息
"""
import json
import logging
import time
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "ts": int(record.created * 1000),  # ms 级时间戳
            "level": record.levelname,
            "msg": record.getMessage(),
            "module": record.module,
            "func": record.funcName,
        }
        # 如果 extra 中带 user 或 cost，一并记录
        if hasattr(record, "user"):
            log_obj["user"] = record.user
        if hasattr(record, "cost"):
            log_obj["cost"] = round(record.cost, 3)  # 秒，保留 3 位
        return json.dumps(log_obj, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """获取已配置好的 JSON 日志器"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger