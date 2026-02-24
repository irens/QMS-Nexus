"""
文件上传接口：异步任务 ID 即刻返回
"""
import asyncio
import hashlib
import uuid
import time
from pathlib import Path
from typing import Dict, Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Body, Query
from pydantic import BaseModel, Field

from services.document_service import DocumentService
from core.metrics import upload_counter, upload_duration
from core.task_store import set_task, get_task
from core.document_version_store import (
    DuplicateType,
    document_version_store,
)
from core.logger import get_logger

router = APIRouter()
svc = DocumentService()
logger = get_logger(__name__)


class UploadResponse(BaseModel):
    task_id: str
    status: str  # Pending / Processing / Completed / Failed
    collection: str  # 目标知识库


# ============ 去重检测 API ============

class DuplicateCheckRequest(BaseModel):
    """去重检测请求"""
    file_hash: str = Field(..., description="文件 SHA256 哈希值")
    filename: str = Field(..., description="文件名")
    kb_id: str = Field(default="default", description="知识库ID")


class DuplicateCheckResponse(BaseModel):
    """去重检测响应"""
    code: int = Field(200, description="响应码")
    message: str = Field("success", description="响应消息")
    data: Optional[dict] = Field(None, description="响应数据")


def _calculate_file_hash(file_content: bytes) -> str:
    """计算文件 SHA256 哈希"""
    return hashlib.sha256(file_content).hexdigest()


@router.post("/upload/check-duplicate", response_model=DuplicateCheckResponse)
async def check_duplicate(request: DuplicateCheckRequest):
    """
    上传前检查文件是否重复

    请求:
    {
      "file_hash": "sha256_hash_string",
      "filename": "GJZ-QP-01.docx",
      "kb_id": "default"
    }

    响应:
    {
      "code": 200,
      "message": "success",
      "data": {
        "type": "exact_match",  // exact_match/name_match/new_file
        "message": "该文件已存在",
        "existing_document": {
          "id": "doc_id",
          "title": "记录控制程序",
          "current_version": {
            "version_id": "ver_id",
            "version_number": 2,
            "version_label": "V2.1",
            "status": "effective"
          }
        },
        "existing_version": {
          "version_id": "ver_id",
          "version_number": 2,
          "version_label": "V2.1",
          "status": "effective",
          "file_hash": "...",
          "created_at": "2024-01-15T10:00:00"
        },
        "suggestions": [
          {"action": "view", "label": "查看现有版本"},
          {"action": "upload_as_new_version", "label": "作为新版本上传"},
          {"action": "force_upload", "label": "强制重新上传"},
          {"action": "cancel", "label": "取消"}
        ]
      }
    }

    检测类型：
    - exact_match: 完全相同的文件（哈希相同）
    - name_match: 同名不同内容（文件名相同，哈希不同）
    - new_file: 新文件
    """
    try:
        result = await document_version_store.check_duplicate(
            file_hash=request.file_hash,
            filename=request.filename,
            kb_id=request.kb_id,
        )

        return DuplicateCheckResponse(
            code=200,
            message="success",
            data={
                "type": result.type.value,
                "message": result.message,
                "existing_document": result.existing_document,
                "existing_version": result.existing_version,
                "suggestions": result.suggestions or [],
            }
        )

    except Exception as e:
        logger.error(f"去重检测失败: {e}")
        raise HTTPException(status_code=500, detail=f"去重检测失败: {str(e)}")


@router.post("/upload/check-duplicate-file", response_model=DuplicateCheckResponse)
async def check_duplicate_file(
    file: UploadFile = File(...),
    kb_id: str = Form(default="default", description="知识库ID"),
):
    """
    上传文件进行去重检测（直接上传文件方式）

    前端可以先调用此接口检测重复，再根据结果决定如何处理
    """
    try:
        # 读取文件内容并计算哈希
        file_content = await file.read()
        file_hash = _calculate_file_hash(file_content)

        # 重置文件指针
        await file.seek(0)

        result = await document_version_store.check_duplicate(
            file_hash=file_hash,
            filename=file.filename,
            kb_id=kb_id,
        )

        return DuplicateCheckResponse(
            code=200,
            message="success",
            data={
                "type": result.type.value,
                "message": result.message,
                "file_hash": file_hash,
                "filename": file.filename,
                "existing_document": result.existing_document,
                "existing_version": result.existing_version,
                "suggestions": result.suggestions or [],
            }
        )

    except Exception as e:
        logger.error(f"文件去重检测失败: {e}")
        raise HTTPException(status_code=500, detail=f"去重检测失败: {str(e)}")


# ============ 上传接口（集成去重检测） ============

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    collection: Optional[str] = Form("qms_docs", description="目标知识库名称"),
    skip_duplicate_check: bool = Query(False, description="是否跳过去重检测"),
    force_upload: bool = Query(False, description="强制上传（需要特殊权限）"),
):
    """
    上传单文件到指定知识库，≤50 MB，即刻返回任务 ID。
    
    修改说明：
    - 默认进行去重检测
    - 如果检测到 exact_match，返回 409 冲突错误，提示使用 check-duplicate 接口
    - 如果 skip_duplicate_check=true 且 force_upload=true，强制上传（需要特殊权限）
    
    Args:
        file: 上传的文件
        collection: 目标知识库名称（默认 qms_docs）
        skip_duplicate_check: 是否跳过去重检测
        force_upload: 强制上传（忽略重复检测，需要特殊权限）
    """
    t0 = time.time()
    status = "ok"
    
    try:
        # 基础校验
        if not file.content_type:
            raise HTTPException(status_code=400, detail="缺少 Content-Type")
        allowed = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                   "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel",
                   "application/vnd.openxmlformats-officedocument.presentationml.presentation"]
        if file.content_type not in allowed:
            raise HTTPException(status_code=400, detail="不支持的文件类型")
        
        # 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)
        
        if file_size > 50 * 1024 * 1024:
            raise HTTPException(status_code=413, detail="文件超过 50 MB")

        # 计算文件哈希
        file_hash = _calculate_file_hash(file_content)
        
        # 重置文件指针
        await file.seek(0)

        # 去重检测（除非跳过）
        if not skip_duplicate_check:
            logger.info(f"执行去重检测: filename={file.filename}, hash={file_hash[:16]}...")
            
            duplicate_check = await document_version_store.check_duplicate(
                file_hash=file_hash,
                filename=file.filename,
                kb_id=collection,
            )

            if duplicate_check.type == DuplicateType.EXACT_MATCH:
                # 完全相同的文件 - 返回 409 冲突
                logger.warning(f"检测到重复文件: {file.filename}, hash={file_hash[:16]}...")
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": "文件已存在",
                        "type": "exact_match",
                        "file_hash": file_hash,
                        "existing_document": duplicate_check.existing_document,
                        "existing_version": duplicate_check.existing_version,
                        "suggestions": duplicate_check.suggestions,
                        "hint": "请使用 /api/v1/upload/check-duplicate 接口获取详细信息"
                    }
                )

            if duplicate_check.type == DuplicateType.NAME_MATCH:
                # 同名不同内容 - 记录日志，但允许上传
                logger.info(f"检测到同名文件: {file.filename}, 内容不同")

        # 创建任务
        task_id = str(uuid.uuid4())
        set_task(task_id, {
            "status": "Pending",
            "filename": file.filename,
            "collection": collection,
            "file_hash": file_hash,
        })

        # 落盘（临时目录）并后台解析
        tmp_dir = Path("./tmp_uploads")
        tmp_dir.mkdir(exist_ok=True)
        file_path = tmp_dir / f"{task_id}_{file.filename}"
        
        with open(file_path, "wb") as f:
            f.write(file_content)

        # 后台解析（阶段三换 Redis+Worker）
        asyncio.create_task(svc.process(task_id, file_path, file.content_type, collection))

        # 记录上传日志
        logger.info(f"文件上传成功: task_id={task_id}, filename={file.filename}, hash={file_hash[:16]}...")

        cost = time.time() - t0
        upload_duration.observe(cost)
        upload_counter.labels(status=status).inc()
        
        return {
            "code": 200,
            "message": "上传成功",
            "data": {
                "task_id": task_id,
                "status": "Pending",
                "collection": collection,
                "file_hash": file_hash,
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


@router.get("/upload/status/{task_id}", response_model=UploadResponse)
def get_status(task_id: str):
    """查询任务状态"""
    t = get_task(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="任务不存在")
    return UploadResponse(
        task_id=task_id,
        status=t["status"],
        collection=t.get("collection", "qms_docs")
    )


# ============ 智能上传接口 ============

@router.post("/upload/smart")
async def smart_upload(
    file: UploadFile = File(...),
    collection: Optional[str] = Form("qms_docs", description="目标知识库名称"),
    document_id: Optional[str] = Form(None, description="文档组ID（创建新版本时提供）"),
    change_summary: Optional[str] = Form(None, description="变更摘要"),
    change_details: Optional[str] = Form(None, description="变更详细说明"),
    version_label: Optional[str] = Form(None, description="版本标签"),
    force_upload: bool = Form(False, description="强制上传（忽略重复检测）"),
):
    """
    智能上传接口（集成去重检测）

    流程：
    1. 计算文件哈希
    2. 检测是否重复
    3. 根据检测结果处理：
       - exact_match: 返回重复提示
       - name_match: 自动创建为新版本（如果提供 document_id）
       - new_file: 正常上传
    """
    t0 = time.time()

    try:
        # 读取文件内容
        file_content = await file.read()
        file_size = len(file_content)
        file_hash = _calculate_file_hash(file_content)

        # 重置文件指针
        await file.seek(0)

        # 去重检测（除非强制上传）
        if not force_upload:
            duplicate_check = await document_version_store.check_duplicate(
                file_hash=file_hash,
                filename=file.filename,
                kb_id=collection,
            )

            if duplicate_check.type == DuplicateType.EXACT_MATCH:
                # 完全相同的文件
                return {
                    "code": 409,
                    "message": "文件已存在",
                    "data": {
                        "type": "exact_match",
                        "file_hash": file_hash,
                        "existing_document": duplicate_check.existing_document,
                        "existing_version": duplicate_check.existing_version,
                        "suggestions": duplicate_check.suggestions,
                    }
                }

            if duplicate_check.type == DuplicateType.NAME_MATCH and not document_id:
                # 同名文件但未提供 document_id
                return {
                    "code": 409,
                    "message": "检测到同名文档",
                    "data": {
                        "type": "name_match",
                        "file_hash": file_hash,
                        "existing_document": duplicate_check.existing_document,
                        "existing_version": duplicate_check.existing_version,
                        "suggestions": duplicate_check.suggestions,
                    }
                }

        # 创建任务
        task_id = str(uuid.uuid4())
        set_task(task_id, {
            "status": "Pending",
            "filename": file.filename,
            "collection": collection,
            "file_hash": file_hash,
        })

        # 如果是新版本上传
        if document_id:
            # 创建新版本
            version = await document_version_store.create_version(
                document_id=document_id,
                filename=file.filename,
                file_hash=file_hash,
                file_size=file_size,
                file_type=file.content_type or "application/octet-stream",
                change_summary=change_summary or "上传新版本",
                change_details=change_details,
                version_label=version_label,
                prepared_by="system",  # TODO: 从认证获取
                kb_id=collection,
            )

            # 更新任务状态
            set_task(task_id, {
                "status": "Completed",
                "filename": file.filename,
                "collection": collection,
                "version_id": version.id,
                "version_number": version.version_number,
            })

            cost = time.time() - t0
            upload_duration.observe(cost)
            upload_counter.labels(status="ok").inc()

            return {
                "code": 200,
                "message": "新版本创建成功",
                "data": {
                    "task_id": task_id,
                    "status": "Completed",
                    "collection": collection,
                    "version_id": version.id,
                    "version_number": version.version_number,
                    "version_label": version.version_label,
                    "status": version.status,
                }
            }

        # 正常上传流程
        tmp_dir = Path("./tmp_uploads")
        tmp_dir.mkdir(exist_ok=True)
        file_path = tmp_dir / f"{task_id}_{file.filename}"

        with open(file_path, "wb") as f:
            f.write(file_content)

        # 后台解析
        asyncio.create_task(svc.process(task_id, file_path, file.content_type, collection))

        cost = time.time() - t0
        upload_duration.observe(cost)
        upload_counter.labels(status="ok").inc()

        return {
            "code": 200,
            "message": "上传成功",
            "data": {
                "task_id": task_id,
                "status": "Pending",
                "collection": collection,
                "file_hash": file_hash,
            }
        }

    except Exception as e:
        logger.error(f"智能上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")
