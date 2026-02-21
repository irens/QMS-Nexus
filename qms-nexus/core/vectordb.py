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

    async def upsert_chunks(self, chunks: List[Chunk], collection: str = "qms_docs") -> List[str]:
        """批量写入或更新 chunks 到指定知识库，返回 ids。"""
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
    ) -> List[SearchResult]:
        """异步语义检索，支持标签过滤和知识库选择。"""
        coll = self._get_collection(collection)
        where = None
        if filter_tags:
            # 单标签直接字段过滤；多标签用 $or
            if len(filter_tags) == 1:
                where = {"tags": {"$contains": filter_tags[0]}}
            else:
                where = {"$or": [{"tags": {"$contains": tag}} for tag in filter_tags]}

        res = coll.query(
            query_texts=[query],
            n_results=top_k,
            where=where,
        )
        results = []
        for doc, meta, score in zip(
            res["documents"][0], res["metadatas"][0], res["distances"][0]
        ):
            results.append(
                SearchResult(
                    text=doc,
                    score=1 - score,  # cosine → 相似度
                    source=f"[来源：{meta.get('filename')}, 第{meta.get('page')}页]",
                    tags=meta.get("tags", []),
                    metadata=meta,
                )
            )
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
