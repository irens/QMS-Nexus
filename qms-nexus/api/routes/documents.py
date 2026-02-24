"""
文档管理路由
提供文档的 CRUD 操作和查询功能（基于 SQLite 持久化存储）。
"""
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from core.config import settings
from core.document_store import DocumentNotFoundError, document_store
from core.logger import get_logger
from core.vectordb import VectorDBClient
from core.database import DocumentVersion, db_manager

router = APIRouter()
logger = get_logger(__name__)

# 初始化 VectorDB 客户端
vectordb = VectorDBClient(persist_dir=settings.CHROMA_PERSIST_DIR)


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


class DocumentVersionOut(BaseModel):
    """文档版本信息输出模型"""
    id: str
    versionNumber: int
    versionLabel: Optional[str]
    status: str
    effectiveDate: Optional[str] = None
    reviewDate: Optional[str] = None
    previousVersionId: Optional[str] = None
    changeSummary: Optional[str] = None
    preparedBy: Optional[str] = None
    approvedBy: Optional[str] = None
    approvedDate: Optional[str] = None


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
    currentVersion: Optional[DocumentVersionOut] = None


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
    includeVersion: bool = Query(True, description="是否包含当前版本信息"),
):
    """获取文档列表，支持分页、搜索和筛选"""
    # 解析时间范围
    def _parse_dt(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    start_dt = _parse_dt(startDate)
    end_dt = _parse_dt(endDate)

    docs, total = document_store.list_documents(
        page=page,
        page_size=pageSize,
        search=search,
        file_types=fileType,
        tags=tags,
        statuses=status,
        start_date=start_dt,
        end_date=end_dt,
        sort_by=sortBy,
        sort_order=sortOrder,
        include_version=includeVersion,
    )

    total_pages = (total + pageSize - 1) // pageSize if pageSize else 1

    return DocumentListResponse(
        items=[_document_to_out(d) for d in docs],
        total=total,
        page=page,
        pageSize=pageSize,
        totalPages=total_pages,
    )


@router.post("/documents", response_model=DocumentOut)
async def create_document(body: DocumentCreate):
    """创建新文档记录"""
    doc = document_store.create(
        filename=body.filename,
        file_type=body.fileType,
        file_size=body.fileSize,
        tags=body.tags,
        metadata=body.metadata,
    )
    logger.info(f"创建文档记录: {doc.id} - {body.filename}")

    return _document_to_out(doc)


@router.get("/documents/{document_id}", response_model=DocumentOut)
async def get_document(document_id: str):
    """获取单个文档详情"""
    doc = document_store.get_by_id(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    return _document_to_out(doc)


@router.delete("/documents/{document_id}")
async def delete_document(document_id: str):
    """删除单个文档"""
    doc = document_store.get_by_id(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 从 VectorDB 中删除相关 chunks
    try:
        await vectordb.delete_by_filename(doc.filename)
    except Exception as exc:
        logger.warning(f"从 VectorDB 删除文档失败: {exc}")

    try:
        document_store.delete(document_id)
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="文档不存在")

    logger.info(f"删除文档: {document_id}")

    return {"detail": "文档已删除"}


@router.delete("/documents")
async def batch_delete_documents(body: BatchDeleteRequest):
    """批量删除文档"""
    deleted_count = 0
    not_found: List[str] = []

    for doc_id in body.documentIds:
        doc = document_store.get_by_id(doc_id)
        if doc is None:
            not_found.append(doc_id)
            continue

        try:
            await vectordb.delete_by_filename(doc.filename)
        except Exception as exc:
            logger.warning(f"从 VectorDB 删除文档失败: {exc}")

        try:
            document_store.delete(doc_id)
            deleted_count += 1
        except DocumentNotFoundError:
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
    try:
        doc = document_store.update_tags_for_document(document_id, body.tags)
    except DocumentNotFoundError:
        raise HTTPException(status_code=404, detail="文档不存在")

    logger.info(f"更新文档标签: {document_id}")
    return _document_to_out(doc)


@router.get("/documents/{document_id}/download")
async def download_document(document_id: str):
    """下载文档（返回文档信息，实际文件下载由前端处理）"""
    doc = document_store.get_by_id(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    return {
        "documentId": document_id,
        "filename": doc.filename,
        "fileType": doc.file_type,
        "fileSize": doc.file_size,
        "downloadUrl": f"/api/v1/documents/{document_id}/file"
    }


@router.get("/documents/{document_id}/preview")
async def preview_document(document_id: str, page: Optional[int] = None):
    """预览文档内容"""
    doc = document_store.get_by_id(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    
    # 这里应该返回文档的文本内容
    # 实际实现中可能需要从 VectorDB 获取 chunks
    return {
        "documentId": document_id,
        "filename": doc.filename,
        "page": page,
        "content": f"文档 {doc.filename} 的预览内容（第 {page or 1} 页）",
    }


@router.get("/documents/{document_id}/related")
async def get_related_documents(document_id: str, limit: int = Query(5, ge=1, le=20)):
    """获取相关文档"""
    doc = document_store.get_by_id(document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 简单的相关文档算法：相同标签或相同文件类型的其他文档
    from core.database import Document as DocumentModel
    from core.database import db_manager

    with db_manager.get_session() as session:
        current_tags = {t.name for t in doc.tags}
        candidates = (
            session.query(DocumentModel)
            .filter(DocumentModel.id != document_id)
            .all()
        )

        related = []
        for other in candidates:
            score = 0
            if other.file_type == doc.file_type:
                score += 1
            common_tags = current_tags & {t.name for t in other.tags}
            score += len(common_tags) * 2
            if score > 0:
                related.append({"document": other, "score": score})

    related.sort(key=lambda x: x["score"], reverse=True)
    related = related[:limit]

    return [_document_to_out(r["document"]) for r in related]


@router.get("/documents/stats", response_model=DocumentStats)
async def get_document_stats():
    """获取文档统计信息"""
    stats = document_store.get_stats()

    return DocumentStats(
        total=stats["total"],
        byType=stats["byType"],
        byStatus=stats["byStatus"],
        byTag=stats["byTag"],
        recentUploads=stats["recentUploads"],
    )


@router.put("/documents/batch/status")
async def batch_update_status(body: BatchUpdateStatusRequest):
    """批量更新文档状态"""
    updated_count, not_found = document_store.update_status_batch(
        body.documentIds, body.status
    )
    logger.info(f"批量更新文档状态: 成功 {updated_count}, 未找到 {len(not_found)}")

    return {
        "detail": f"已更新 {updated_count} 个文档的状态",
        "updated": updated_count,
        "notFound": not_found
    }


@router.put("/documents/batch/tags")
async def batch_update_tags(body: BatchUpdateTagsRequest):
    """批量更新文档标签"""
    updated_count, not_found = document_store.update_tags_batch(
        body.documentIds, body.tags, body.operation
    )
    logger.info(f"批量更新文档标签: 成功 {updated_count}, 未找到 {len(not_found)}")

    return {
        "detail": f"已更新 {updated_count} 个文档的标签",
        "updated": updated_count,
        "notFound": not_found
    }


def _version_to_out(version: Optional[DocumentVersion]) -> Optional[DocumentVersionOut]:
    """将 ORM DocumentVersion 模型转换为响应对象。"""
    if version is None:
        return None
    
    return DocumentVersionOut(
        id=version.id,
        versionNumber=version.version_number,
        versionLabel=version.version_label,
        status=version.status,
        effectiveDate=version.effective_date.isoformat() if version.effective_date else None,
        reviewDate=version.review_date.isoformat() if version.review_date else None,
        previousVersionId=version.previous_version_id,
        changeSummary=version.change_summary,
        preparedBy=version.prepared_by,
        approvedBy=version.approved_by,
        approvedDate=version.approved_date.isoformat() if version.approved_date else None,
    )


def _document_to_out(doc) -> DocumentOut:
    """将 ORM Document 模型转换为响应对象。"""

    upload_time = doc.upload_time or doc.created_at
    upload_time_str = upload_time.isoformat() if upload_time else datetime.utcnow().isoformat()

    try:
        import json

        metadata = json.loads(doc.metadata_json) if doc.metadata_json else {}
    except Exception:
        metadata = {}

    tag_names = [t.name for t in getattr(doc, "tags", [])]
    
    # 获取当前版本信息
    current_version = getattr(doc, "current_version", None)

    return DocumentOut(
        id=doc.id,
        filename=doc.filename,
        fileType=doc.file_type or "",
        fileSize=doc.file_size or 0,
        uploadTime=upload_time_str,
        status=doc.status or "Pending",
        tags=tag_names,
        metadata=metadata,
        chunksCount=doc.chunks_count,
        parseTime=doc.parse_time,
        errorMessage=doc.error_message,
        currentVersion=_version_to_out(current_version),
    )
