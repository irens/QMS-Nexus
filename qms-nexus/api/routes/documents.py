"""
文档管理路由
提供文档的 CRUD 操作和查询功能
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
import uuid
import os

from core.vectordb import VectorDBClient
from core.config import settings
from core.logger import get_logger

router = APIRouter()
logger = get_logger(__name__)

# 初始化 VectorDB 客户端
vectordb = VectorDBClient(persist_dir=settings.CHROMA_PERSIST_DIR)

# 内存级文档存储（实际项目中应该使用数据库）
documents_store: dict = {}


class DocumentCreate(BaseModel):
    filename: str
    fileType: str
    fileSize: int
    tags: List[str] = []
    metadata: dict = {}


class DocumentUpdate(BaseModel):
    filename: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None


class DocumentOut(BaseModel):
    id: str
    filename: str
    fileType: str
    fileSize: int
    uploadTime: str
    status: str
    tags: List[str]
    metadata: dict
    chunksCount: Optional[int] = None
    parseTime: Optional[float] = None
    errorMessage: Optional[str] = None


class DocumentListResponse(BaseModel):
    items: List[DocumentOut]
    total: int
    page: int
    pageSize: int
    totalPages: int


class DocumentStats(BaseModel):
    total: int
    byType: dict
    byStatus: dict
    byTag: dict
    recentUploads: int


class BatchDeleteRequest(BaseModel):
    documentIds: List[str]


class BatchUpdateStatusRequest(BaseModel):
    documentIds: List[str]
    status: str


class BatchUpdateTagsRequest(BaseModel):
    documentIds: List[str]
    tags: List[str]
    operation: str = "add"  # add, remove, replace


class UpdateDocumentTagsRequest(BaseModel):
    tags: List[str]


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    fileType: Optional[List[str]] = Query(None),
    tags: Optional[List[str]] = Query(None),
    status: Optional[List[str]] = Query(None),
    startDate: Optional[str] = None,
    endDate: Optional[str] = None,
    sortBy: str = Query("uploadTime", pattern="^(uploadTime|fileName|fileSize)$"),
    sortOrder: str = Query("desc", pattern="^(asc|desc)$"),
):
    """获取文档列表，支持分页、搜索和筛选"""
    items = list(documents_store.values())
    
    # 搜索过滤
    if search:
        items = [d for d in items if search.lower() in d["filename"].lower()]
    
    # 文件类型过滤
    if fileType:
        items = [d for d in items if d["fileType"] in fileType]
    
    # 标签过滤
    if tags:
        items = [d for d in items if any(tag in d.get("tags", []) for tag in tags)]
    
    # 状态过滤
    if status:
        items = [d for d in items if d["status"] in status]
    
    # 日期范围过滤
    if startDate:
        items = [d for d in items if d["uploadTime"] >= startDate]
    if endDate:
        items = [d for d in items if d["uploadTime"] <= endDate]
    
    # 排序
    reverse = sortOrder == "desc"
    if sortBy == "uploadTime":
        items.sort(key=lambda x: x["uploadTime"], reverse=reverse)
    elif sortBy == "fileName":
        items.sort(key=lambda x: x["filename"].lower(), reverse=reverse)
    elif sortBy == "fileSize":
        items.sort(key=lambda x: x["fileSize"], reverse=reverse)
    
    total = len(items)
    totalPages = (total + pageSize - 1) // pageSize
    
    start = (page - 1) * pageSize
    end = start + pageSize
    items = items[start:end]
    
    return DocumentListResponse(
        items=[DocumentOut(**d) for d in items],
        total=total,
        page=page,
        pageSize=pageSize,
        totalPages=totalPages
    )


@router.post("/documents", response_model=DocumentOut)
async def create_document(body: DocumentCreate):
    """创建新文档记录"""
    doc_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    
    document = {
        "id": doc_id,
        "filename": body.filename,
        "fileType": body.fileType,
        "fileSize": body.fileSize,
        "uploadTime": now,
        "status": "Pending",
        "tags": body.tags,
        "metadata": body.metadata,
        "chunksCount": None,
        "parseTime": None,
        "errorMessage": None,
    }
    
    documents_store[doc_id] = document
    logger.info(f"创建文档记录: {doc_id} - {body.filename}")
    
    return DocumentOut(**document)


@router.get("/documents/{document_id}", response_model=DocumentOut)
async def get_document(document_id: str):
    """获取单个文档详情"""
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return DocumentOut(**documents_store[document_id])


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """删除单个文档"""
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    doc = documents_store[document_id]
    
    # 从 VectorDB 中删除相关 chunks
    try:
        await vectordb.delete_by_filename(doc["filename"])
    except Exception as e:
        logger.warning(f"从 VectorDB 删除文档失败: {e}")
    
    del documents_store[document_id]
    logger.info(f"删除文档: {document_id}")
    
    return {"detail": "文档已删除"}


@router.delete("/documents")
async def batch_delete_documents(body: BatchDeleteRequest):
    """批量删除文档"""
    deleted_count = 0
    not_found = []
    
    for doc_id in body.documentIds:
        if doc_id in documents_store:
            doc = documents_store[doc_id]
            
            # 从 VectorDB 中删除相关 chunks
            try:
                await vectordb.delete_by_filename(doc["filename"])
            except Exception as e:
                logger.warning(f"从 VectorDB 删除文档失败: {e}")
            
            del documents_store[doc_id]
            deleted_count += 1
        else:
            not_found.append(doc_id)
    
    logger.info(f"批量删除文档: 成功 {deleted_count}, 未找到 {len(not_found)}")
    
    return {
        "detail": f"已删除 {deleted_count} 个文档",
        "deleted": deleted_count,
        "notFound": not_found
    }


@router.put("/documents/{document_id}/tags", response_model=DocumentOut)
async def update_document_tags(document_id: str, body: UpdateDocumentTagsRequest):
    """更新文档标签"""
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    documents_store[document_id]["tags"] = body.tags
    logger.info(f"更新文档标签: {document_id}")
    
    return DocumentOut(**documents_store[document_id])


@router.get("/documents/{document_id}/download")
async def download_document(document_id: str):
    """下载文档（返回文档信息，实际文件下载由前端处理）"""
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    doc = documents_store[document_id]
    
    return {
        "documentId": document_id,
        "filename": doc["filename"],
        "fileType": doc["fileType"],
        "fileSize": doc["fileSize"],
        "downloadUrl": f"/api/v1/documents/{document_id}/file"
    }


@router.get("/documents/{document_id}/preview")
async def preview_document(document_id: str, page: Optional[int] = None):
    """预览文档内容"""
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    doc = documents_store[document_id]
    
    # 这里应该返回文档的文本内容
    # 实际实现中可能需要从 VectorDB 获取 chunks
    return {
        "documentId": document_id,
        "filename": doc["filename"],
        "page": page,
        "content": f"文档 {doc['filename']} 的预览内容（第 {page or 1} 页）"
    }


@router.get("/documents/{document_id}/related")
async def get_related_documents(document_id: str, limit: int = Query(5, ge=1, le=20)):
    """获取相关文档"""
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    doc = documents_store[document_id]
    
    # 简单的相关文档算法：相同标签或相同文件类型的其他文档
    related = []
    for other_id, other_doc in documents_store.items():
        if other_id == document_id:
            continue
        
        # 计算相关性分数
        score = 0
        if other_doc["fileType"] == doc["fileType"]:
            score += 1
        
        common_tags = set(other_doc.get("tags", [])) & set(doc.get("tags", []))
        score += len(common_tags) * 2
        
        if score > 0:
            related.append({"document": other_doc, "score": score})
    
    # 按相关性排序并限制数量
    related.sort(key=lambda x: x["score"], reverse=True)
    related = related[:limit]
    
    return [DocumentOut(**r["document"]) for r in related]


@router.get("/documents/stats", response_model=DocumentStats)
async def get_document_stats():
    """获取文档统计信息"""
    items = list(documents_store.values())
    
    # 按类型统计
    by_type = {}
    for doc in items:
        file_type = doc["fileType"]
        by_type[file_type] = by_type.get(file_type, 0) + 1
    
    # 按状态统计
    by_status = {}
    for doc in items:
        status = doc["status"]
        by_status[status] = by_status.get(status, 0) + 1
    
    # 按标签统计
    by_tag = {}
    for doc in items:
        for tag in doc.get("tags", []):
            by_tag[tag] = by_tag.get(tag, 0) + 1
    
    # 最近上传（7天内）
    from datetime import timedelta
    now = datetime.now()
    recent_uploads = sum(
        1 for doc in items
        if datetime.fromisoformat(doc["uploadTime"]) > now - timedelta(days=7)
    )
    
    return DocumentStats(
        total=len(items),
        byType=by_type,
        byStatus=by_status,
        byTag=by_tag,
        recentUploads=recent_uploads
    )


@router.put("/documents/batch/status")
async def batch_update_status(body: BatchUpdateStatusRequest):
    """批量更新文档状态"""
    updated_count = 0
    not_found = []
    
    for doc_id in body.documentIds:
        if doc_id in documents_store:
            documents_store[doc_id]["status"] = body.status
            updated_count += 1
        else:
            not_found.append(doc_id)
    
    logger.info(f"批量更新文档状态: 成功 {updated_count}, 未找到 {len(not_found)}")
    
    return {
        "detail": f"已更新 {updated_count} 个文档的状态",
        "updated": updated_count,
        "notFound": not_found
    }


@router.put("/documents/batch/tags")
async def batch_update_tags(body: BatchUpdateTagsRequest):
    """批量更新文档标签"""
    updated_count = 0
    not_found = []
    
    for doc_id in body.documentIds:
        if doc_id in documents_store:
            doc = documents_store[doc_id]
            current_tags = set(doc.get("tags", []))
            new_tags = set(body.tags)
            
            if body.operation == "add":
                current_tags.update(new_tags)
            elif body.operation == "remove":
                current_tags -= new_tags
            elif body.operation == "replace":
                current_tags = new_tags
            
            doc["tags"] = list(current_tags)
            updated_count += 1
        else:
            not_found.append(doc_id)
    
    logger.info(f"批量更新文档标签: 成功 {updated_count}, 未找到 {len(not_found)}")
    
    return {
        "detail": f"已更新 {updated_count} 个文档的标签",
        "updated": updated_count,
        "notFound": not_found
    }
