"""
问答日志记录与查询。

依赖统一的 chat_logs 表，提供记录每次 /ask 调用的接口，
以及后台分页查询接口。
"""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from core.database import ChatLog, db_manager


class ChatLogger:
    """问答日志管理器。"""

    def log_chat(
        self,
        *,
        user_id: Optional[str],
        kb_id: Optional[str],
        question: str,
        answer: str,
        sources: List[str],
        is_corrected: bool,
        correction_id: Optional[int],
        response_time_ms: int,
        model_used: Optional[str],
        tokens_used: Optional[int],
        ip_address: Optional[str],
    ) -> None:
        """
        写入一条问答日志。
        """

        with db_manager.get_session() as session:
            row = ChatLog(
                id=str(uuid.uuid4()),
                user_id=user_id,
                kb_id=kb_id or "default",
                question=question,
                answer=answer,
                sources_json=json.dumps(sources or [], ensure_ascii=False),
                is_corrected=is_corrected,
                correction_id=correction_id,
                response_time_ms=response_time_ms,
                model_used=model_used,
                tokens_used=tokens_used,
                ip_address=ip_address,
            )
            session.add(row)
            session.flush()

    def query_logs(
        self,
        *,
        page: int,
        page_size: int,
        user_id: Optional[str] = None,
        kb_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        search: Optional[str] = None,
    ) -> Tuple[List[ChatLog], int]:
        """按条件查询问答日志。"""

        with db_manager.get_session() as session:
            query = session.query(ChatLog)

            if user_id:
                query = query.filter(ChatLog.user_id == user_id)
            if kb_id:
                query = query.filter(ChatLog.kb_id == kb_id)
            if start_time:
                query = query.filter(ChatLog.created_at >= start_time)
            if end_time:
                query = query.filter(ChatLog.created_at <= end_time)
            if search:
                like = f"%{search}%"
                query = query.filter(ChatLog.question.ilike(like))

            total = query.count()
            query = query.order_by(ChatLog.created_at.desc())

            offset = (page - 1) * page_size
            items = query.offset(offset).limit(page_size).all()

            return items, int(total)


chat_logger = ChatLogger()

