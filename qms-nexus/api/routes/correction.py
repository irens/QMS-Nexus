"""
修正库管理接口
提供修正记录的 CRUD 操作
"""
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.correction_service import correction_service

router = APIRouter(tags=["correction"])


class CorrectionCreate(BaseModel):
    question: str
    correct_answer: str
    original_answer: Optional[str] = None
    source_doc: Optional[str] = None
    page_number: Optional[int] = None


class CorrectionUpdate(BaseModel):
    correct_answer: Optional[str] = None
    is_active: Optional[bool] = None
    source_doc: Optional[str] = None
    page_number: Optional[int] = None


class CorrectionOut(BaseModel):
    id: int
    question: str
    correct_answer: str
    original_answer: Optional[str]
    source_doc: Optional[str]
    page_number: Optional[int]
    created_at: str
    updated_at: str
    is_active: bool


class PaginatedCorrections(BaseModel):
    items: List[CorrectionOut]
    total: int
    limit: int
    offset: int


@router.post("/corrections", response_model=dict)
async def create_correction(body: CorrectionCreate):
    """创建新的修正记录"""
    try:
        correction_id = correction_service.add_correction(
            question=body.question,
            correct_answer=body.correct_answer,
            original_answer=body.original_answer,
            source_doc=body.source_doc,
            page_number=body.page_number
        )
        return {"id": correction_id, "message": "修正记录已创建"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/corrections", response_model=PaginatedCorrections)
async def list_corrections(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    is_active: Optional[bool] = Query(None, description="是否激活"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """获取修正记录列表"""
    result = correction_service.search_corrections(
        keyword=keyword,
        is_active=is_active,
        limit=limit,
        offset=offset
    )
    return PaginatedCorrections(
        items=result["items"],
        total=result["total"],
        limit=limit,
        offset=offset
    )


@router.get("/corrections/{correction_id}", response_model=CorrectionOut)
async def get_correction(correction_id: int):
    """获取单个修正记录"""
    correction = correction_service.get_correction_by_id(correction_id)
    if not correction:
        raise HTTPException(status_code=404, detail="修正记录不存在")
    return correction


@router.put("/corrections/{correction_id}", response_model=dict)
async def update_correction(correction_id: int, body: CorrectionUpdate):
    """更新修正记录"""
    success = correction_service.update_correction(
        correction_id=correction_id,
        correct_answer=body.correct_answer,
        is_active=body.is_active,
        source_doc=body.source_doc,
        page_number=body.page_number
    )
    if not success:
        raise HTTPException(status_code=404, detail="修正记录不存在或无需更新")
    return {"message": "修正记录已更新"}


@router.delete("/corrections/{correction_id}", response_model=dict)
async def delete_correction(correction_id: int, hard: bool = Query(False, description="是否硬删除")):
    """删除修正记录（默认软删除）"""
    if hard:
        success = correction_service.hard_delete_correction(correction_id)
    else:
        success = correction_service.delete_correction(correction_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="修正记录不存在")
    return {"message": "修正记录已删除"}


@router.get("/corrections/stats", response_model=dict)
async def get_correction_stats():
    """获取修正库统计信息"""
    return correction_service.get_stats()
