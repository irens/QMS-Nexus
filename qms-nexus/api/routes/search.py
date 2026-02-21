"""
检索接口：支持 ?q=&filter_tags=&collection=
"""
import time
from typing import List, Optional

from fastapi import APIRouter, Query
from pydantic import BaseModel

from core.vectordb import VectorDBClient
from core.metrics import search_counter, search_duration

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
    collection: str = Query("qms_docs", description="知识库名称"),
    top_k: int = Query(5, ge=1, le=100),
):
    """
    语义检索，支持知识库选择和标签过滤
    
    Args:
        q: 查询文本
        filter_tags: 标签过滤列表
        collection: 知识库名称（默认 qms_docs）
        top_k: 返回结果数量
    """
    t0 = time.time()
    status = "ok"
    try:
        results = await client.similarity_search(
            q, 
            top_k=top_k, 
            filter_tags=filter_tags,
            collection=collection
        )
    except Exception:
        status = "error"
        raise
    finally:
        search_duration.observe(time.time() - t0)
        search_counter.labels(status=status).inc()
    return [
        SearchResult(
            text=r.text,
            source=r.source,
            tags=r.tags,
            score=r.score,
        )
        for r in results
    ]
