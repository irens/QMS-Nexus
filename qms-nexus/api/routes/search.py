"""
检索接口：支持 ?q=&filter_tags=
"""
from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from core.vectordb import VectorDBClient

router = APIRouter()
client = VectorDBClient()


class SearchResult(BaseModel):
    text: str
    source: str
    tags: List[str]
    score: float


@router.get("/search", response_model=List[SearchResult])
async def search(
    q: str = Query(..., description="查询文本"),
    filter_tags: Optional[List[str]] = Query(None, description="标签过滤"),
    top_k: int = Query(5, ge=1, le=100),
):
    """语义检索，返回带标签的结果。"""
    results = await client.similarity_search(q, top_k=top_k, filter_tags=filter_tags)
    return [
        SearchResult(
            text=r.text,
            source=r.source,
            tags=r.tags,
            score=r.score,
        )
        for r in results
    ]