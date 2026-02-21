"""
知识库管理接口
提供知识库的 CRUD 操作
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from core.knowledge_base import kb_service

router = APIRouter(tags=["knowledge-base"])


class KnowledgeBaseCreate(BaseModel):
    id: str = Field(..., pattern=r"^[a-zA-Z][a-zA-Z0-9_]*$", 
                    description="知识库唯一标识，以字母开头，只能包含字母、数字和下划线")
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field(default="", max_length=500)


class KnowledgeBaseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)


class KnowledgeBaseOut(BaseModel):
    id: str
    name: str
    description: str
    collection_name: str
    created_at: str
    updated_at: str
    is_active: bool
    document_count: int


@router.post("/knowledge-bases", response_model=dict)
async def create_kb(body: KnowledgeBaseCreate):
    """创建新的知识库"""
    try:
        success = kb_service.create_kb(
            kb_id=body.id,
            name=body.name,
            description=body.description
        )
        if not success:
            raise HTTPException(status_code=409, detail="知识库ID已存在")
        return {"id": body.id, "message": "知识库创建成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/knowledge-bases", response_model=List[KnowledgeBaseOut])
async def list_kbs(include_inactive: bool = Query(False)):
    """获取知识库列表"""
    return kb_service.list_kbs(include_inactive=include_inactive)


@router.get("/knowledge-bases/{kb_id}", response_model=KnowledgeBaseOut)
async def get_kb(kb_id: str):
    """获取单个知识库信息"""
    kb = kb_service.get_kb(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return kb


@router.put("/knowledge-bases/{kb_id}", response_model=dict)
async def update_kb(kb_id: str, body: KnowledgeBaseUpdate):
    """更新知识库信息"""
    try:
        success = kb_service.update_kb(
            kb_id=kb_id,
            name=body.name,
            description=body.description
        )
        if not success:
            raise HTTPException(status_code=404, detail="知识库不存在或无需更新")
        return {"message": "知识库更新成功"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/knowledge-bases/{kb_id}", response_model=dict)
async def delete_kb(kb_id: str, hard: bool = Query(False, description="是否硬删除")):
    """删除知识库"""
    try:
        if hard:
            success = kb_service.hard_delete_kb(kb_id)
        else:
            success = kb_service.delete_kb(kb_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="知识库不存在")
        return {"message": "知识库已删除"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/knowledge-bases/{kb_id}/switch", response_model=dict)
async def switch_kb(kb_id: str):
    """切换当前使用的知识库（客户端使用）"""
    kb = kb_service.get_kb(kb_id)
    if not kb:
        raise HTTPException(status_code=404, detail="知识库不存在")
    return {
        "message": "知识库切换成功",
        "kb_id": kb_id,
        "collection_name": kb["collection_name"]
    }
