"""
动态标签 CRUD
"""
from typing import List, Dict
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# 内存级标签池（阶段三换 DB）
tags_pool: Dict[str, str] = {}  # tag -> description


class TagCreate(BaseModel):
    tag: str
    description: str = ""


class TagUpdate(BaseModel):
    description: str


class TagOut(BaseModel):
    tag: str
    description: str


@router.post("/tags", response_model=TagOut)
async def create_tag(body: TagCreate):
    """新增标签。"""
    if body.tag in tags_pool:
        raise HTTPException(status_code=409, detail="标签已存在")
    tags_pool[body.tag] = body.description
    return TagOut(tag=body.tag, description=body.description)


@router.get("/tags", response_model=List[TagOut])
async def list_tags():
    """列出全部标签。"""
    return [TagOut(tag=k, description=v) for k, v in tags_pool.items()]


@router.get("/tags/{tag}", response_model=TagOut)
async def get_tag(tag: str):
    """获取单个标签。"""
    if tag not in tags_pool:
        raise HTTPException(status_code=404, detail="标签不存在")
    return TagOut(tag=tag, description=tags_pool[tag])


@router.put("/tags/{tag}", response_model=TagOut)
async def update_tag(tag: str, body: TagUpdate):
    """更新标签描述。"""
    if tag not in tags_pool:
        raise HTTPException(status_code=404, detail="标签不存在")
    tags_pool[tag] = body.description
    return TagOut(tag=tag, description=body.description)


@router.delete("/tags/{tag}")
async def delete_tag(tag: str):
    """删除标签。"""
    if tag not in tags_pool:
        raise HTTPException(status_code=404, detail="标签不存在")
    del tags_pool[tag]
    return {"detail": "已删除"}