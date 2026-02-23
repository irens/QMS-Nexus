"""
动态标签 CRUD（基于数据库存储）

保持现有 API 接口不变，仅将内存存储迁移到 SQLite。
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.database import Tag
from core.tag_store import TagAlreadyExistsError, TagNotFoundError, tag_store

router = APIRouter()


class TagCreate(BaseModel):
    name: str
    description: str = ""
    color: str = "#409EFF"


class TagUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None


class TagOut(BaseModel):
    id: str
    name: str
    description: str
    color: str
    usageCount: int
    createdAt: str
    updatedAt: str


class TagListResponse(BaseModel):
    items: List[TagOut]
    total: int
    page: int
    pageSize: int
    totalPages: int


@router.post("/tags", response_model=TagOut)
async def create_tag(body: TagCreate):
    """新增标签"""
    try:
        tag = tag_store.create(
            name=body.name,
            description=body.description,
            color=body.color,
        )
    except TagAlreadyExistsError:
        raise HTTPException(status_code=409, detail="标签已存在")

    return _tag_to_out(tag)


@router.get("/tags", response_model=TagListResponse)
async def list_tags(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
):
    """列出全部标签"""
    offset = (page - 1) * pageSize
    tags, total = tag_store.list_all(search=search, offset=offset, limit=pageSize)
    total_pages = (total + pageSize - 1) // pageSize if pageSize else 1

    return TagListResponse(
        items=[_tag_to_out(t) for t in tags],
        total=total,
        page=page,
        pageSize=pageSize,
        totalPages=total_pages,
    )


@router.get("/tags/stats")
async def get_tag_stats():
    """获取标签统计"""
    tags, _ = tag_store.list_all()
    items = [_tag_to_out(t) for t in tags]

    most_used = sorted(items, key=lambda x: x.usageCount, reverse=True)[:5]
    recently_created = sorted(items, key=lambda x: x.createdAt, reverse=True)[:5]

    return {
        "totalTags": len(items),
        "totalDocuments": sum(t.usageCount for t in items),
        "averageDocumentsPerTag": (
            sum(t.usageCount for t in items) / len(items) if items else 0
        ),
        "mostUsedTags": [
            {"tagId": t.id, "tagName": t.name, "documentCount": t.usageCount}
            for t in most_used
        ],
        "recentlyCreated": recently_created,
    }


@router.get("/tags/search")
async def search_tags(
    query: str = Query(...),
    limit: int = Query(10, ge=1, le=100),
):
    """搜索标签"""
    tags, _ = tag_store.list_all(search=query)
    # 按使用次数排序，取前 limit 个
    tags_sorted = sorted(tags, key=lambda t: t.usage_count or 0, reverse=True)[:limit]
    return [_tag_to_out(t) for t in tags_sorted]


@router.get("/tags/{tag_id}", response_model=TagOut)
async def get_tag(tag_id: str):
    """获取单个标签"""
    tag = tag_store.get_by_id(tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail="标签不存在")
    return _tag_to_out(tag)


@router.put("/tags/{tag_id}", response_model=TagOut)
async def update_tag(tag_id: str, body: TagUpdate):
    """更新标签"""
    try:
        tag = tag_store.update(
            tag_id,
            name=body.name,
            description=body.description,
            color=body.color,
        )
    except TagNotFoundError:
        raise HTTPException(status_code=404, detail="标签不存在")
    except TagAlreadyExistsError:
        raise HTTPException(status_code=409, detail="标签已存在")

    return _tag_to_out(tag)


@router.delete("/tags/{tag_id}")
async def delete_tag(tag_id: str):
    """删除标签"""
    try:
        tag_store.delete(tag_id)
    except TagNotFoundError:
        raise HTTPException(status_code=404, detail="标签不存在")
    return {"detail": "已删除"}


@router.get("/tags/{tag_id}/documents")
async def get_tagged_documents(
    tag_id: str,
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
):
    """获取标签下的文档"""
    # 目前仅校验标签是否存在，文档关联由文档存储模块维护
    if tag_store.get_by_id(tag_id) is None:
        raise HTTPException(status_code=404, detail="标签不存在")
    
    return {
        "items": [],
        "total": 0,
        "page": page,
        "pageSize": pageSize,
        "totalPages": 0,
    }


def _tag_to_out(tag: Tag) -> TagOut:
    """将 ORM Tag 模型转换为响应对象。"""

    created_at = tag.created_at.isoformat() if getattr(tag, "created_at", None) else ""
    updated_at = tag.updated_at.isoformat() if getattr(tag, "updated_at", None) else ""

    return TagOut(
        id=tag.id,
        name=tag.name,
        description=tag.description or "",
        color=tag.color or "#409EFF",
        usageCount=tag.usage_count or 0,
        createdAt=created_at,
        updatedAt=updated_at,
    )
