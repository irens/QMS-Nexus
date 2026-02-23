"""
系统日志存储与查询。

职责：
- 使用 TimedRotatingFileHandler 将系统日志写入 ./logs/system/ 目录
- 同步写入数据库表 system_logs，便于前端分页检索
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from logging.handlers import TimedRotatingFileHandler

from core.config import settings
from core.database import SystemLog, db_manager


class LogStore:
    """系统日志管理器，负责文件和数据库双写，以及查询接口。"""

    def __init__(self) -> None:
        self._logger = self._init_logger()

    def _init_logger(self) -> logging.Logger:
        """初始化系统日志 logger。"""

        log_dir = Path(settings.LOG_DIR) / "system"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "system.log"

        logger = logging.getLogger("qms.system")
        logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO))

        if not any(isinstance(h, TimedRotatingFileHandler) for h in logger.handlers):
            handler = TimedRotatingFileHandler(
                filename=str(log_file),
                when="midnight",
                interval=1,
                backupCount=settings.LOG_RETENTION_DAYS,
                encoding="utf-8",
                utc=False,
            )
            # 日志格式：时间|级别|模块|消息|用户ID|请求ID
            formatter = logging.Formatter(
                fmt="%(asctime)s|%(levelname)s|%(module)s|%(message)s|%(user_id)s|%(request_id)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    # ---------------- 公共方法 ----------------
    def log(
        self,
        *,
        level: str,
        module: str,
        message: str,
        user_id: Optional[str] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        记录一条系统日志，写入文件并同步写入数据库。
        """

        level_name = level.upper()
        level_num = getattr(logging, level_name, logging.INFO)
        extra = {
            "user_id": user_id or "",
            "request_id": request_id or "",
        }

        # 写入文件
        self._logger.log(level_num, message, extra=extra)

        # 写入数据库
        with db_manager.get_session() as session:
            log_row = SystemLog(
                level=level_name,
                module=module,
                message=message,
                user_id=user_id,
                request_id=request_id,
                ip_address=ip_address,
                metadata_json=json.dumps(metadata or {}, ensure_ascii=False),
            )
            session.add(log_row)
            session.flush()

    def query_logs(
        self,
        *,
        page: int,
        page_size: int,
        level: Optional[str] = None,
        module: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[SystemLog], int]:
        """
        按条件查询系统日志，返回 (items, total)。
        """

        with db_manager.get_session() as session:
            query = session.query(SystemLog)

            if level:
                query = query.filter(SystemLog.level == level.upper())
            if module:
                query = query.filter(SystemLog.module == module)
            if start_time:
                query = query.filter(SystemLog.created_at >= start_time)
            if end_time:
                query = query.filter(SystemLog.created_at <= end_time)
            if search:
                like = f"%{search}%"
                query = query.filter(SystemLog.message.ilike(like))

            total = query.count()
            query = query.order_by(SystemLog.created_at.desc())

            offset = (page - 1) * page_size
            items = query.offset(offset).limit(page_size).all()

            return items, int(total)


# 全局实例
log_store = LogStore()

