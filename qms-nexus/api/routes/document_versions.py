"""
文档版本管理路由
提供文档版本的完整生命周期管理 API
"""
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field

from core.database import (
    Document,
    DocumentApprovalHistory,
    DocumentVersion,
    db_manager,
)
from core.document_version_store import (
    DuplicateCheckResult,
    DuplicateType,
    InvalidStatusTransitionError,
    VersionNotFoundError,
    document_version_store,
)
from core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# 上传文件存储目录
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


# ============ Pydantic 模型 ============

class StandardResponse(BaseModel):
    """标准响应格式"""
    code: int = 200
    message: str = "success"
    data: Optional[dict] = None


class VersionOut(BaseModel):
    """版本信息输出模型"""
    id: str
    document_id: str
    version_number: int
    version_label: str
    filename: str
    file_hash: str
    file_size: int
    file_type: str
    status: str
    title: Optional[str]
    description: Optional[str]
    change_summary: Optional[str]
    change_details: Optional[str]
    previous_version_id: Optional[str]
    effective_date: Optional[str]
    review_date: Optional[str]
    is_latest: bool
    prepared_by: Optional[str]
    reviewed_by: Optional[str]
    approved_by: Optional[str]
    approved_date: Optional[str]
    kb_id: str
    created_by: Optional[str]
    created_at: str
    updated_at: str


class VersionListResponse(BaseModel):
    """版本列表响应"""
    items: List[VersionOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class VersionDetailOut(BaseModel):
    """版本详情输出模型"""
    version: VersionOut
    approval_history: List[dict]
    previous_version: Optional[VersionOut]


class ApprovalHistoryOut(BaseModel):
    """审批历史输出模型"""
    id: int
    action: str
    action_by: str
    action_at: str
    comment: Optional[str]
    from_status: Optional[str]
    to_status: str


class VersionCompareOut(BaseModel):
    """版本对比输出模型"""
    v1_id: str
    v2_id: str
    v1_version_label: str
    v2_version_label: str
    added: List[dict]
    removed: List[dict]
    modified: List[dict]
    statistics: dict


class ApproveRequest(BaseModel):
    """审批通过请求"""
    comment: Optional[str] = Field(None, description="审批意见")
    current_user: str = Field(..., description="当前用户")


class RejectRequest(BaseModel):
    """审批拒绝请求"""
    comment: str = Field(..., description="拒绝原因（必填）")
    current_user: str = Field(..., description="当前用户")


class ObsoleteRequest(BaseModel):
    """作废版本请求"""
    reason: Optional[str] = Field(None, description="作废原因")
    current_user: str = Field(..., description="当前用户")


class SubmitRequest(BaseModel):
    """提交审核请求"""
    comment: Optional[str] = Field(None, description="提交说明")
    current_user: str = Field(..., description="当前用户")


# ============ 辅助函数 ============

def _version_to_out(version: DocumentVersion) -> VersionOut:
    """将 DocumentVersion ORM 对象转换为输出模型"""
    return VersionOut(
        id=version.id,
        document_id=version.document_id,
        version_number=version.version_number,
        version_label=version.version_label or f"V{version.version_number}.0",
        filename=version.filename,
        file_hash=version.file_hash,
        file_size=version.file_size or 0,
        file_type=version.file_type or "",
        status=version.status,
        title=version.title,
        description=version.description,
        change_summary=version.change_summary,
        change_details=version.change_details,
        previous_version_id=version.previous_version_id,
        effective_date=version.effective_date.isoformat() if version.effective_date else None,
        review_date=version.review_date.isoformat() if version.review_date else None,
        is_latest=version.is_latest or False,
        prepared_by=version.prepared_by,
        reviewed_by=version.reviewed_by,
        approved_by=version.approved_by,
        approved_date=version.approved_date.isoformat() if version.approved_date else None,
        kb_id=version.kb_id or "default",
        created_by=version.created_by,
        created_at=version.created_at.isoformat() if version.created_at else "",
        updated_at=version.updated_at.isoformat() if version.updated_at else "",
    )


def _approval_history_to_out(history: DocumentApprovalHistory) -> dict:
    """将审批历史 ORM 对象转换为字典"""
    return {
        "id": history.id,
        "action": history.action,
        "action_by": history.action_by,
        "action_at": history.action_at.isoformat() if history.action_at else "",
        "comment": history.comment,
        "from_status": history.from_status,
        "to_status": history.to_status,
    }


def _calculate_file_hash(file_content: bytes) -> str:
    """计算文件 SHA256 哈希"""
    return hashlib.sha256(file_content).hexdigest()


def _save_upload_file(file: UploadFile, version_id: str) -> Path:
    """保存上传的文件"""
    file_content = file.file.read()
    file_path = UPLOAD_DIR / f"{version_id}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(file_content)
    file.file.seek(0)
    return file_path, file_content


# ============ API 接口 ============

@router.post("/{document_id}/versions", response_model=StandardResponse)
async def create_document_version(
    document_id: str,
    file: UploadFile = File(...),
    change_summary: str = Form(..., description="变更摘要（必填）"),
    change_details: Optional[str] = Form(None, description="变更详细说明"),
    version_label: Optional[str] = Form(None, description="版本标签，如 V2.1"),
    effective_date: Optional[str] = Form(None, description="生效日期（ISO格式）"),
    current_user: str = Form("system", description="当前用户"),
):
    """
    上传新版本
    - 自动检测文件哈希
    - 自动递增版本号
    - 状态设为 draft
    - 记录编制人
    """
    try:
        # 保存文件并计算哈希
        file_path, file_content = _save_upload_file(file, "temp")
        file_hash = _calculate_file_hash(file_content)
        file_size = len(file_content)
        file_type = file.content_type or "application/octet-stream"

        # 重新生成版本ID并保存文件
        version_id = os.urandom(16).hex()
        final_path = UPLOAD_DIR / f"{version_id}_{file.filename}"
        os.rename(file_path, final_path)

        # 解析生效日期
        parsed_effective_date = None
        if effective_date:
            try:
                parsed_effective_date = datetime.fromisoformat(effective_date.replace("Z", "+00:00"))
            except ValueError:
                pass

        # 创建新版本
        version = await document_version_store.create_version(
            document_id=document_id,
            filename=file.filename,
            file_hash=file_hash,
            file_size=file_size,
            file_type=file_type,
            change_summary=change_summary,
            change_details=change_details,
            version_label=version_label,
            prepared_by=current_user,
            kb_id="default",
        )

        # 更新生效日期（如果提供）
        if parsed_effective_date:
            with db_manager.get_session() as session:
                version_obj = session.get(DocumentVersion, version.id)
                if version_obj:
                    version_obj.effective_date = parsed_effective_date
                    session.commit()

        return StandardResponse(
            code=200,
            message="版本创建成功",
            data={
                "version_id": version.id,
                "version_number": version.version_number,
                "version_label": version.version_label,
                "status": version.status,
                "file_hash": file_hash,
            }
        )

    except Exception as e:
        logger.error(f"创建版本失败: {e}")
        raise HTTPException(status_code=500, detail=f"创建版本失败: {str(e)}")


@router.get("/{document_id}/versions", response_model=StandardResponse)
async def list_document_versions(
    document_id: str,
    status: Optional[str] = Query(None, description="按状态筛选"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort_by: str = Query("version_number", description="排序字段: version_number/created_at"),
    sort_order: str = Query("desc", description="排序方向: asc/desc"),
):
    """
    获取文档版本历史列表
    - 支持分页
    - 支持按状态筛选
    - 支持排序
    """
    try:
        with db_manager.get_session() as session:
            from sqlalchemy import desc, asc

            # 构建查询
            query = session.query(DocumentVersion).filter(
                DocumentVersion.document_id == document_id
            )

            if status:
                query = query.filter(DocumentVersion.status == status)

            # 获取总数
            total = query.count()

            # 排序
            sort_column = getattr(DocumentVersion, sort_by, DocumentVersion.version_number)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))

            # 分页
            offset = (page - 1) * page_size
            versions = query.offset(offset).limit(page_size).all()

            total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

            return StandardResponse(
                code=200,
                message="success",
                data={
                    "items": [_version_to_out(v) for v in versions],
                    "total": total,
                    "page": page,
                    "page_size": page_size,
                    "total_pages": total_pages,
                }
            )

    except Exception as e:
        logger.error(f"获取版本列表失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取版本列表失败: {str(e)}")


@router.get("/versions/{version_id}", response_model=StandardResponse)
async def get_version_detail(version_id: str):
    """
    获取版本详情
    - 包含版本元数据
    - 包含审批历史
    - 包含上一版本信息（如有）
    """
    try:
        # 获取版本信息
        version = await document_version_store.get_version_by_id(version_id)
        if not version:
            raise HTTPException(status_code=404, detail="版本不存在")

        # 获取审批历史
        approval_history = await document_version_store.get_approval_history(version_id)

        # 获取上一版本信息
        previous_version = None
        if version.previous_version_id:
            previous_version = await document_version_store.get_version_by_id(
                version.previous_version_id
            )

        return StandardResponse(
            code=200,
            message="success",
            data={
                "version": _version_to_out(version),
                "approval_history": [_approval_history_to_out(h) for h in approval_history],
                "previous_version": _version_to_out(previous_version) if previous_version else None,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取版本详情失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取版本详情失败: {str(e)}")


@router.post("/versions/{version_id}/approve", response_model=StandardResponse)
async def approve_version(
    version_id: str,
    request: ApproveRequest,
):
    """
    审批通过版本
    - 验证当前状态为 approved 或 review（根据流程）
    - 更新状态为 effective
    - 将上一版本标记为 obsolete
    - 设置 is_latest=true
    - 记录审批人、审批时间
    - 记录审批历史
    """
    current_user = request.current_user
    try:
        # 检查版本是否存在
        version = await document_version_store.get_version_by_id(version_id)
        if not version:
            raise HTTPException(status_code=404, detail="版本不存在")

        # 验证状态（当前实现：approved -> effective）
        if version.status not in ["approved", "review"]:
            raise HTTPException(
                status_code=400,
                detail=f"版本状态必须是 approved 或 review，当前状态: {version.status}"
            )

        # 如果当前是 review 状态，先转为 approved
        if version.status == "review":
            await document_version_store.update_version_status(
                version_id=version_id,
                new_status="approved",
                user_id=current_user,
                comment="审核通过，等待批准",
            )

        # 审批通过（approved -> effective）
        success = await document_version_store.approve_version(
            version_id=version_id,
            approved_by=current_user,
            comment=request.comment,
        )

        if success:
            return StandardResponse(
                code=200,
                message="版本审批通过",
                data={
                    "version_id": version_id,
                    "status": "effective",
                    "approved_by": current_user,
                    "approved_at": datetime.utcnow().isoformat(),
                }
            )
        else:
            raise HTTPException(status_code=500, detail="审批失败")

    except HTTPException:
        raise
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"审批版本失败: {e}")
        raise HTTPException(status_code=500, detail=f"审批失败: {str(e)}")


@router.post("/versions/{version_id}/reject", response_model=StandardResponse)
async def reject_version(
    version_id: str,
    request: RejectRequest,
):
    """
    审批拒绝，返回 draft 状态
    - 验证当前状态为 review
    - 状态变更为 draft
    - 记录拒绝原因
    """
    current_user = request.current_user
    try:
        # 检查版本是否存在
        version = await document_version_store.get_version_by_id(version_id)
        if not version:
            raise HTTPException(status_code=404, detail="版本不存在")

        # 验证当前状态为 review
        if version.status != "review":
            raise HTTPException(
                status_code=400,
                detail=f"版本状态必须是 review，当前状态: {version.status}"
            )

        # 拒绝版本（review -> draft）
        success = await document_version_store.update_version_status(
            version_id=version_id,
            new_status="draft",
            user_id=current_user,
            comment=f"审批拒绝: {request.comment}",
        )

        if success:
            return StandardResponse(
                code=200,
                message="版本已退回草稿状态",
                data={
                    "version_id": version_id,
                    "status": "draft",
                    "reject_reason": request.comment,
                    "rejected_by": current_user,
                    "rejected_at": datetime.utcnow().isoformat(),
                }
            )
        else:
            raise HTTPException(status_code=500, detail="拒绝失败")

    except HTTPException:
        raise
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"拒绝版本失败: {e}")
        raise HTTPException(status_code=500, detail=f"拒绝失败: {str(e)}")


@router.post("/versions/{version_id}/obsolete", response_model=StandardResponse)
async def obsolete_version(
    version_id: str,
    request: ObsoleteRequest,
):
    """
    作废版本（需要质量经理权限）
    - 验证用户权限
    - 状态变更为 obsolete
    - 如果是当前生效版本，需要指定替代版本
    - 记录作废原因
    """
    current_user = request.current_user
    try:
        # TODO: 验证用户权限（质量经理）
        # 这里简化处理，实际应该检查用户角色

        # 检查版本是否存在
        version = await document_version_store.get_version_by_id(version_id)
        if not version:
            raise HTTPException(status_code=404, detail="版本不存在")

        # 验证当前状态允许作废
        if version.status not in ["effective", "approved"]:
            raise HTTPException(
                status_code=400,
                detail=f"只有 effective 或 approved 状态的版本可以作废，当前状态: {version.status}"
            )

        # 作废版本
        success = await document_version_store.obsolete_version(
            version_id=version_id,
            user_id=current_user,
            reason=request.reason or "版本作废",
        )

        if success:
            return StandardResponse(
                code=200,
                message="版本已作废",
                data={
                    "version_id": version_id,
                    "status": "obsolete",
                    "reason": request.reason,
                    "obsoleted_by": current_user,
                    "obsoleted_at": datetime.utcnow().isoformat(),
                }
            )
        else:
            raise HTTPException(status_code=500, detail="作废失败")

    except HTTPException:
        raise
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"作废版本失败: {e}")
        raise HTTPException(status_code=500, detail=f"作废失败: {str(e)}")


@router.get("/versions/{v1_id}/compare/{v2_id}", response_model=StandardResponse)
async def compare_versions(v1_id: str, v2_id: str):
    """
    对比两个版本差异
    - 获取两个版本的文本内容
    - 使用 difflib 找出差异
    - 返回结构化差异数据
    """
    try:
        # 获取版本对比结果
        diff_result = await document_version_store.compare_versions(v1_id, v2_id)

        # 计算统计信息
        added_count = len(diff_result.added_chunks)
        removed_count = len(diff_result.removed_chunks)
        modified_count = len(diff_result.modified_chunks)

        return StandardResponse(
            code=200,
            message="success",
            data={
                "v1_id": diff_result.v1_id,
                "v2_id": diff_result.v2_id,
                "v1_version_label": diff_result.v1_version_label,
                "v2_version_label": diff_result.v2_version_label,
                "added": diff_result.added_chunks,
                "removed": diff_result.removed_chunks,
                "modified": diff_result.modified_chunks,
                "statistics": {
                    "added_count": added_count,
                    "removed_count": removed_count,
                    "modified_count": modified_count,
                },
                "change_summary": diff_result.change_summary,
            }
        )

    except VersionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"版本对比失败: {e}")
        raise HTTPException(status_code=500, detail=f"版本对比失败: {str(e)}")


@router.get("/versions/{version_id}/download")
async def download_version(version_id: str):
    """
    下载特定版本的原始文件
    - 验证版本存在
    - 返回文件流
    - 记录下载日志
    """
    try:
        # 获取版本信息
        version = await document_version_store.get_version_by_id(version_id)
        if not version:
            raise HTTPException(status_code=404, detail="版本不存在")

        # 查找文件
        file_pattern = f"{version_id}_*"
        matching_files = list(UPLOAD_DIR.glob(file_pattern))

        if not matching_files:
            raise HTTPException(status_code=404, detail="文件不存在")

        file_path = matching_files[0]

        # 记录下载日志
        logger.info(f"版本文件下载: version_id={version_id}, filename={version.filename}")

        from fastapi.responses import FileResponse

        return FileResponse(
            path=file_path,
            filename=version.filename,
            media_type=version.file_type or "application/octet-stream",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"下载版本失败: {e}")
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")


# ============ 额外辅助接口 ============

@router.post("/versions/{version_id}/submit", response_model=StandardResponse)
async def submit_version_for_review(
    version_id: str,
    request: SubmitRequest,
):
    """
    提交版本进行审核（draft -> review）
    """
    current_user = request.current_user
    comment = request.comment
    try:
        version = await document_version_store.get_version_by_id(version_id)
        if not version:
            raise HTTPException(status_code=404, detail="版本不存在")

        if version.status != "draft":
            raise HTTPException(
                status_code=400,
                detail=f"只有 draft 状态的版本可以提交审核，当前状态: {version.status}"
            )

        success = await document_version_store.update_version_status(
            version_id=version_id,
            new_status="review",
            user_id=current_user,
            comment=comment or "提交审核",
        )

        if success:
            return StandardResponse(
                code=200,
                message="版本已提交审核",
                data={
                    "version_id": version_id,
                    "status": "review",
                    "submitted_by": current_user,
                    "submitted_at": datetime.utcnow().isoformat(),
                }
            )
        else:
            raise HTTPException(status_code=500, detail="提交审核失败")

    except HTTPException:
        raise
    except InvalidStatusTransitionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"提交审核失败: {e}")
        raise HTTPException(status_code=500, detail=f"提交审核失败: {str(e)}")
