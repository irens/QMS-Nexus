"""
聊天问答相关路由（目前仅提供日志查询接口）。
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from core.chat_logger import chat_logger


router = APIRouter()


class ChatLogItem(BaseModel):
    id: str
    userId: Optional[str]
    kbId: Optional[str]
    question: str
    answer: str
    sources: List[str]
    isCorrected: bool
    correctionId: Optional[int]
    responseTimeMs: Optional[int]
    modelUsed: Optional[str]
    tokensUsed: Optional[int]
    ipAddress: Optional[str]
    createdAt: str


class ChatLogPage(BaseModel):
    items: List[ChatLogItem]
    total: int
    page: int
    pageSize: int
    totalPages: int


@router.get("/chat/logs", response_model=ChatLogPage)
async def list_chat_logs(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    userId: Optional[str] = None,
    kbId: Optional[str] = None,
    startTime: Optional[str] = None,
    endTime: Optional[str] = None,
    search: Optional[str] = None,
):
    """查询问答日志。"""

    def _parse_dt(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    start_dt = _parse_dt(startTime)
    end_dt = _parse_dt(endTime)

    rows, total = chat_logger.query_logs(
        page=page,
        page_size=pageSize,
        user_id=userId,
        kb_id=kbId,
        start_time=start_dt,
        end_time=end_dt,
        search=search,
    )

    total_pages = (total + pageSize - 1) // pageSize if pageSize else 1

    def _row_to_item(row) -> ChatLogItem:
        import json

        try:
            sources = json.loads(row.sources_json) if row.sources_json else []
        except Exception:
            sources = []

        return ChatLogItem(
            id=row.id,
            userId=row.user_id,
            kbId=row.kb_id,
            question=row.question,
            answer=row.answer,
            sources=sources,
            isCorrected=row.is_corrected,
            correctionId=row.correction_id,
            responseTimeMs=row.response_time_ms,
            modelUsed=row.model_used,
            tokensUsed=row.tokens_used,
            ipAddress=row.ip_address,
            createdAt=row.created_at.isoformat() if row.created_at else "",
        )

    return ChatLogPage(
        items=[_row_to_item(r) for r in rows],
        total=total,
        page=page,
        pageSize=pageSize,
        totalPages=total_pages,
    )

