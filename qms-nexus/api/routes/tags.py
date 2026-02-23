"""
动态标签 CRUD
"""
from typing import List, Dict, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import uuid

router = APIRouter()

tags_store: Dict[str, dict] = {}


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
    for t in tags_store.values():
        if t["name"] == body.name:
            raise HTTPException(status_code=409, detail="标签已存在")
    
    tag_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    tags_store[tag_id] = {
        "id": tag_id,
        "name": body.name,
        "description": body.description,
        "color": body.color,
        "usageCount": 0,
        "createdAt": now,
        "updatedAt": now,
    }
    return TagOut(**tags_store[tag_id])


@router.get("/tags", response_model=TagListResponse)
async def list_tags(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
):
    """列出全部标签"""
    items = list(tags_store.values())
    
    if search:
        items = [t for t in items if search.lower() in t["name"].lower()]
    
    total = len(items)
    totalPages = (total + pageSize - 1) // pageSize
    
    start = (page - 1) * pageSize
    end = start + pageSize
    items = items[start:end]
    
    return TagListResponse(
        items=[TagOut(**t) for t in items],
        total=total,
        page=page,
        pageSize=pageSize,
        totalPages=totalPages
    )


@router.get("/tags/stats")
async def get_tag_stats():
    """获取标签统计"""
    items = list(tags_store.values())
    most_used = sorted(items, key=lambda x: x["usageCount"], reverse=True)[:5]
    recently_created = sorted(items, key=lambda x: x["createdAt"], reverse=True)[:5]
    
    return {
        "totalTags": len(items),
        "totalDocuments": sum(t["usageCount"] for t in items),
        "averageDocumentsPerTag": sum(t["usageCount"] for t in items) / len(items) if items else 0,
        "mostUsedTags": [
            {"tagId": t["id"], "tagName": t["name"], "documentCount": t["usageCount"]}
            for t in most_used
        ],
        "recentlyCreated": [TagOut(**t) for t in recently_created]
    }


@router.get("/tags/search")
async def search_tags(
    query: str = Query(...),
    limit: int = Query(10, ge=1, le=100),
):
    """搜索标签"""
    items = [t for t in tags_store.values() if query.lower() in t["name"].lower()]
    items = sorted(items, key=lambda x: x["usageCount"], reverse=True)[:limit]
    return [TagOut(**t) for t in items]


@router.get("/tags/{tag_id}", response_model=TagOut)
async def get_tag(tag_id: str):
    """获取单个标签"""
    if tag_id not in tags_store:
        raise HTTPException(status_code=404, detail="标签不存在")
    return TagOut(**tags_store[tag_id])


@router.put("/tags/{tag_id}", response_model=TagOut)
async def update_tag(tag_id: str, body: TagUpdate):
    """更新标签"""
    if tag_id not in tags_store:
        raise HTTPException(status_code=404, detail="标签不存在")
    
    tag = tags_store[tag_id]
    if body.name is not None:
        tag["name"] = body.name
    if body.description is not None:
        tag["description"] = body.description
    if body.color is not None:
        tag["color"] = body.color
    tag["updatedAt"] = datetime.now().isoformat()
    
    return TagOut(**tag)


@router.delete("/tags/{tag_id}")
async def delete_tag(tag_id: str):
    """删除标签"""
    if tag_id not in tags_store:
        raise HTTPException(status_code=404, detail="标签不存在")
    del tags_store[tag_id]
    return {"detail": "已删除"}


@router.get("/tags/{tag_id}/documents")
async def get_tagged_documents(
    tag_id: str,
    page: int = Query(1, ge=1),
    pageSize: int = Query(10, ge=1, le=100),
):
    """获取标签下的文档"""
    if tag_id not in tags_store:
        raise HTTPException(status_code=404, detail="标签不存在")
    
    return {
        "items": [],
        "total": 0,
        "page": page,
        "pageSize": pageSize,
        "totalPages": 0,
    }
