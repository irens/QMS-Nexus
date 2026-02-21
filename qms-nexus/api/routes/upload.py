"""
文件上传接口：异步任务 ID 即刻返回
"""
import asyncio
import uuid
import time
from pathlib import Path
from typing import Dict, Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel

from services.document_service import DocumentService
from core.metrics import upload_counter, upload_duration

router = APIRouter()
svc = DocumentService()

# 内存级任务存储（阶段二后续换 Redis）
tasks: Dict[str, dict] = {}


class UploadResponse(BaseModel):
    task_id: str
    status: str  # Pending / Processing / Completed / Failed
    collection: str  # 目标知识库


@router.post("/upload", response_model=UploadResponse)
async def upload(
    file: UploadFile = File(...),
    collection: Optional[str] = Form("qms_docs", description="目标知识库名称")
):
    """
    上传单文件到指定知识库，≤50 MB，即刻返回任务 ID。
    
    Args:
        file: 上传的文件
        collection: 目标知识库名称（默认 qms_docs）
    """
    t0 = time.time()
    status = "ok"
    # 基础校验
    if not file.content_type:
        raise HTTPException(status_code=400, detail="缺少 Content-Type")
    allowed = ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
               "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.ms-excel",
               "application/vnd.openxmlformats-officedocument.presentationml.presentation"]
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="不支持的文件类型")
    size = file.size or 0
    if size > 50 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="文件超过 50 MB")

    task_id = str(uuid.uuid4())
    tasks[task_id] = {"status": "Pending", "filename": file.filename, "collection": collection}

    # 落盘（临时目录）并后台解析
    tmp_dir = Path("./tmp_uploads")
    tmp_dir.mkdir(exist_ok=True)
    file_path = tmp_dir / f"{task_id}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # 后台解析（阶段三换 Redis+Worker）
    # TODO: 将 collection 传递到 document_service
    asyncio.create_task(svc.process(task_id, file_path, file.content_type, collection))

    cost = time.time() - t0
    upload_duration.observe(cost)
    upload_counter.labels(status=status).inc()
    return UploadResponse(task_id=task_id, status="Pending", collection=collection)


@router.get("/upload/status/{task_id}", response_model=UploadResponse)
def get_status(task_id: str):
    """查询任务状态"""
    t = tasks.get(task_id)
    if not t:
        raise HTTPException(status_code=404, detail="任务不存在")
    return UploadResponse(
        task_id=task_id, 
        status=t["status"],
        collection=t.get("collection", "qms_docs")
    )
