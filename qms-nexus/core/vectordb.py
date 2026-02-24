"""
ChromaDB 异步连接池封装，支持持久化与元数据过滤。
支持多知识库（Multi-Collection）
"""
import os
import uuid
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings
from chromadb.api.models.Collection import Collection

from core.models import Chunk, SearchResult, EmbeddingConfig


class VectorDBClient:
    """线程安全的 ChromaDB 客户端，支持异步上下文和多知识库。"""

    def __init__(self, persist_dir: str = "./chroma_data", embedding_config: EmbeddingConfig = None):
        self.persist_dir = persist_dir
        self.embedding_config = embedding_config or EmbeddingConfig()
        self._client: Optional[chromadb.Client] = None
        self._collections: Dict[str, Collection] = {}  # 缓存多个 collection

    def _get_client(self) -> chromadb.Client:
        if self._client is None:
            self._client = chromadb.Client(
                Settings(
                    persist_directory=self.persist_dir,
                    anonymized_telemetry=False,
                )
            )
        return self._client

    def _get_collection(self, collection_name: str = "qms_docs") -> Collection:
        """获取或创建指定名称的 collection"""
        if collection_name not in self._collections:
            client = self._get_client()
            self._collections[collection_name] = client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        return self._collections[collection_name]

    async def upsert_chunks(
        self,
        chunks: List[Chunk],
        collection: str = "qms_docs",
        version_metadata: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """批量写入或更新 chunks 到指定知识库，返回 ids。

        Args:
            chunks: 文本块列表
            collection: 知识库名称
            version_metadata: 版本元数据，包含 version_id, version_number, version_label, status, effective_date, is_latest 等
        """
        coll = self._get_collection(collection)
        ids = [c.id or str(uuid.uuid4()) for c in chunks]
        texts = [c.text for c in chunks]

        def _build_meta(c: Chunk) -> dict:
            meta = {
                "filename": c.metadata.get("filename"),
                "page": c.page,
                "table": c.table,
                **c.metadata,
            }
            # ChromaDB 不允许空 list，仅在有标签时写入
            tags = c.metadata.get("tags")
            if tags:
                meta["tags"] = tags

            # 添加版本元数据（如果提供）
            if version_metadata:
                meta["version_id"] = version_metadata.get("version_id")
                meta["version_number"] = version_metadata.get("version_number")
                meta["version_label"] = version_metadata.get("version_label")
                meta["status"] = version_metadata.get("status")
                meta["effective_date"] = version_metadata.get("effective_date")
                meta["is_latest"] = version_metadata.get("is_latest")

            return meta

        metas = [_build_meta(c) for c in chunks]
        coll.upsert(ids=ids, documents=texts, metadatas=metas)
        return ids

    async def similarity_search(
        self,
        query: str,
        top_k: int = 5,
        filter_tags: Optional[List[str]] = None,
        collection: str = "qms_docs",
        version_filter: Optional[Dict[str, Any]] = None,
    ) -> List[SearchResult]:
        """异步语义检索，支持标签过滤、知识库选择和版本过滤。

        Args:
            query: 查询文本
            top_k: 返回结果数量
            filter_tags: 标签过滤
            collection: 知识库名称
            version_filter: 版本过滤条件，如 {"is_latest": True, "status": "effective"}
        """
        coll = self._get_collection(collection)
        where = {}

        # 标签过滤
        if filter_tags:
            if len(filter_tags) == 1:
                where["tags"] = {"$contains": filter_tags[0]}
            else:
                where["$or"] = [{"tags": {"$contains": tag}} for tag in filter_tags]

        # 版本过滤
        if version_filter:
            for key, value in version_filter.items():
                where[key] = value

        # 如果 where 为空，设为 None
        if not where:
            where = None

        res = coll.query(
            query_texts=[query],
            n_results=top_k,
            where=where,
        )
        results = []
        for doc, meta, score in zip(
            res["documents"][0], res["metadatas"][0], res["distances"][0]
        ):
            # 构建来源信息，包含版本标签
            version_label = meta.get("version_label")
            version_info = f" {version_label}" if version_label else ""
            source = f"[来源：{meta.get('filename')}{version_info}, 第{meta.get('page')}页]"

            results.append(
                SearchResult(
                    text=doc,
                    score=1 - score,  # cosine → 相似度
                    source=source,
                    tags=meta.get("tags", []),
                    metadata=meta,
                )
            )
        return results

    async def get_chunks_by_version(
        self,
        version_id: str,
        collection: str = "qms_docs",
    ) -> List[SearchResult]:
        """获取指定版本的所有chunks。

        Args:
            version_id: 版本ID
            collection: 知识库名称

        Returns:
            该版本的所有文本块列表
        """
        coll = self._get_collection(collection)
        res = coll.get(
            where={"version_id": version_id},
            include=["documents", "metadatas"],
        )

        results = []
        for doc_id, doc, meta in zip(
            res["ids"], res["documents"], res["metadatas"]
        ):
            # 构建来源信息
            version_label = meta.get("version_label")
            version_info = f" {version_label}" if version_label else ""
            source = f"[来源：{meta.get('filename')}{version_info}, 第{meta.get('page')}页]"

            results.append(
                SearchResult(
                    text=doc,
                    score=1.0,  # 直接获取的chunks默认分数为1.0
                    source=source,
                    tags=meta.get("tags", []),
                    metadata={**meta, "chunk_id": doc_id},
                )
            )

        # 按页码排序
        results.sort(key=lambda x: x.metadata.get("page", 0))
        return results

    async def delete_by_filename(self, filename: str, collection: str = "qms_docs") -> int:
        """按文件名从指定知识库删除，返回删除条数。"""
        coll = self._get_collection(collection)
        existing = coll.get(where={"filename": filename})
        if existing["ids"]:
            coll.delete(ids=existing["ids"])
        return len(existing["ids"])

    async def list_collections(self) -> List[str]:
        """列出所有知识库（collection）名称"""
        client = self._get_client()
        collections = client.list_collections()
        return [c.name for c in collections]

    async def delete_collection(self, collection: str) -> bool:
        """删除指定知识库（谨慎使用）"""
        if collection == "qms_docs":
            raise ValueError("不能删除默认知识库")
        try:
            client = self._get_client()
            client.delete_collection(name=collection)
            # 从缓存中移除
            if collection in self._collections:
                del self._collections[collection]
            return True
        except Exception:
            return False

    async def ping(self) -> bool:
        """健康检查。"""
        try:
            self._get_client().heartbeat()
            return True
        except Exception:
            return False
