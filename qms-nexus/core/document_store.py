from __future__ import annotations

"""
文档存储封装。

使用 SQLAlchemy ORM 管理 `documents` 表及其与标签的关联，
为路由层提供统一的文档 CRUD 和查询能力。
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Tuple

import json
import uuid
from sqlalchemy import and_, func, select

from core.database import Document, Tag, db_manager


class DocumentNotFoundError(Exception):
    """文档不存在时抛出。"""


class DocumentStore:
    """文档存储抽象，封装所有与文档相关的数据库操作。"""

    def __init__(self) -> None:
        self._db = db_manager

    # -------- 基础 CRUD --------
    def create(
        self,
        *,
        filename: str,
        file_type: str,
        file_size: int,
        tags: Sequence[str],
        metadata: Dict[str, Any],
    ) -> Document:
        """
        创建文档记录，并维护标签关联及 usage_count。
        """

        upload_time = datetime.utcnow()

        with self._db.get_session() as session:
            doc = Document(id=str(uuid.uuid4()))
            doc.filename = filename
            doc.file_type = file_type
            doc.file_size = file_size
            doc.upload_time = upload_time
            doc.status = "Pending"
            doc.metadata_json = json.dumps(metadata or {}, ensure_ascii=False)

            session.add(doc)

            # 处理标签关联
            self._set_tags_for_document(session, doc, list(tags))

            session.flush()
            return doc

    def get_by_id(self, document_id: str) -> Optional[Document]:
        """根据 ID 获取文档，不存在返回 None。"""

        with self._db.get_session() as session:
            return session.get(Document, document_id)

    def delete(self, document_id: str) -> None:
        """
        删除文档，并更新相关标签的 usage_count。
        """

        with self._db.get_session() as session:
            doc = session.get(Document, document_id)
            if doc is None:
                raise DocumentNotFoundError("文档不存在")

            # 减少标签使用计数
            for tag in list(doc.tags):
                tag.usage_count = max((tag.usage_count or 0) - 1, 0)

            session.delete(doc)
            session.flush()

    # -------- 查询与统计 --------
    def list_documents(
        self,
        *,
        page: int,
        page_size: int,
        search: Optional[str] = None,
        file_types: Optional[Sequence[str]] = None,
        tags: Optional[Sequence[str]] = None,
        statuses: Optional[Sequence[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        sort_by: str = "uploadTime",
        sort_order: str = "desc",
    ) -> Tuple[List[Document], int]:
        """
        复杂查询文档列表，支持过滤、排序和分页。

        返回 (items, total)。
        """

        with self._db.get_session() as session:
            stmt = select(Document)

            if search:
                like = f"%{search}%"
                stmt = stmt.where(Document.filename.ilike(like))

            if file_types:
                stmt = stmt.where(Document.file_type.in_(file_types))

            if statuses:
                stmt = stmt.where(Document.status.in_(statuses))

            if start_date:
                stmt = stmt.where(Document.upload_time >= start_date)
            if end_date:
                stmt = stmt.where(Document.upload_time <= end_date)

            if tags:
                # 至少包含一个指定标签
                stmt = stmt.join(Document.tags).where(Tag.name.in_(tags))

            # 去重，避免同一文档因多标签被重复统计
            stmt = stmt.distinct(Document.id)

            # 总数
            count_stmt = select(func.count()).select_from(stmt.subquery())
            total = session.execute(count_stmt).scalar_one() or 0

            # 排序
            desc = sort_order == "desc"
            if sort_by == "fileName":
                order_col = Document.filename
            elif sort_by == "fileSize":
                order_col = Document.file_size
            else:  # uploadTime
                order_col = Document.upload_time

            if desc:
                stmt = stmt.order_by(order_col.desc())
            else:
                stmt = stmt.order_by(order_col.asc())

            # 分页
            offset = (page - 1) * page_size
            stmt = stmt.offset(offset).limit(page_size)

            items = list(session.execute(stmt).scalars())
            return items, int(total)

    def update_status_batch(self, document_ids: Sequence[str], status: str) -> Tuple[int, List[str]]:
        """
        批量更新文档状态。

        Returns:
            (updated_count, not_found_ids)
        """

        with self._db.get_session() as session:
            existing_docs = (
                session.query(Document).filter(Document.id.in_(list(document_ids))).all()
            )
            found_ids = {d.id for d in existing_docs}
            not_found = [doc_id for doc_id in document_ids if doc_id not in found_ids]

            for doc in existing_docs:
                doc.status = status

            session.flush()
            return len(existing_docs), not_found

    def update_tags_for_document(self, document_id: str, tags: Sequence[str]) -> Document:
        """
        覆盖更新单个文档的标签，并维护 usage_count。
        """

        with self._db.get_session() as session:
            doc = session.get(Document, document_id)
            if doc is None:
                raise DocumentNotFoundError("文档不存在")

            self._set_tags_for_document(session, doc, list(tags))
            session.flush()
            return doc

    def update_tags_batch(
        self,
        document_ids: Sequence[str],
        tags: Sequence[str],
        operation: str,
    ) -> Tuple[int, List[str]]:
        """
        批量更新文档标签。

        operation: add/remove/replace
        """

        with self._db.get_session() as session:
            docs = session.query(Document).filter(Document.id.in_(list(document_ids))).all()
            found_ids = {d.id for d in docs}
            not_found = [doc_id for doc_id in document_ids if doc_id not in found_ids]

            tag_names = list(tags)
            for doc in docs:
                current_names = {t.name for t in doc.tags}
                if operation == "add":
                    new_names = list(current_names | set(tag_names))
                elif operation == "remove":
                    new_names = list(current_names - set(tag_names))
                elif operation == "replace":
                    new_names = list(tag_names)
                else:
                    new_names = list(current_names)

                self._set_tags_for_document(session, doc, new_names)

            session.flush()
            return len(docs), not_found

    def get_stats(self) -> Dict[str, Any]:
        """获取文档统计信息，用于 /documents/stats。"""

        with self._db.get_session() as session:
            docs = session.query(Document).all()

            by_type: Dict[str, int] = {}
            by_status: Dict[str, int] = {}
            by_tag: Dict[str, int] = {}

            for doc in docs:
                by_type[doc.file_type] = by_type.get(doc.file_type, 0) + 1
                by_status[doc.status] = by_status.get(doc.status, 0) + 1
                for tag in doc.tags:
                    by_tag[tag.name] = by_tag.get(tag.name, 0) + 1

            # 最近 7 天上传
            from datetime import timedelta

            now = datetime.utcnow()
            recent_uploads = sum(
                1
                for doc in docs
                if doc.upload_time and doc.upload_time > now - timedelta(days=7)
            )

            return {
                "total": len(docs),
                "byType": by_type,
                "byStatus": by_status,
                "byTag": by_tag,
                "recentUploads": recent_uploads,
            }

    # -------- 内部工具 --------
    def _set_tags_for_document(
        self,
        session,
        doc: Document,
        tag_names: List[str],
    ) -> None:
        """
        将文档的标签设置为给定名称集合，并自动维护 usage_count。
        """

        # 现有标签名称
        current_tags = list(doc.tags)
        current_names = {t.name for t in current_tags}
        new_names = set(tag_names)

        # 需要移除的标签
        to_remove = [t for t in current_tags if t.name not in new_names]
        for tag in to_remove:
            doc.tags.remove(tag)
            tag.usage_count = max((tag.usage_count or 0) - 1, 0)

        # 需要新增的标签
        to_add_names = new_names - current_names
        if to_add_names:
            existing_tags = (
                session.query(Tag).filter(Tag.name.in_(list(to_add_names))).all()
            )
            existing_by_name = {t.name: t for t in existing_tags}

            for name in to_add_names:
                tag = existing_by_name.get(name)
                if tag is None:
                    tag = Tag(
                        id=str(__import__("uuid").uuid4()),
                        name=name,
                        description="",
                        color="#409EFF",
                        usage_count=0,
                    )
                    session.add(tag)

                doc.tags.append(tag)
                tag.usage_count = (tag.usage_count or 0) + 1


# 默认实例供路由层复用
document_store = DocumentStore()

