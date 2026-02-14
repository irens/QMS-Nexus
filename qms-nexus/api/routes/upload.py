"""
文件上传接口：异步任务 ID 即刻返回
"""
import asyncio
import uuid
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from services.document_service import DocumentService

router = APIRouter()
svc = DocumentService()

# 内存级任务存储（阶段二后续换 Redis）
tasks: Dict[str, dict] = {}


class UploadResponse(BaseModel):
    task_id: str
    status: str  # Pending / Processing / Completed / Failed


@router.post("/upload", response_model=UploadResponse)
async def upload(file: UploadFile = File(...)):
    """上传单文件，≤50 MB，即刻返回任务 ID。"""
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
    tasks[task_id] = {"status": "Pending", "filename": file.filename}

    # 落盘（临时目录）并后台解析
    tmp_dir = Path("./tmp_uploads")
    tmp_dir.mkdir(exist_ok=True)
    file_path = tmp_dir / f"{task_id}_{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # 后台解析（阶段三换 Redis+Worker）
    asyncio.create_task(svc.process(task_id, file_path, file.content_type))

    return UploadResponse(task_id=task_id, status="Pending")