"""
ChromaDB 向量存储封装
提供插入/检索 + 来源标注
"""
import chromadb
from chromadb.config import Settings
from core.models import DocumentChunk


class ChromaService:
    """异步友好的 ChromaDB 封装"""

    def __init__(self, persist_path: str = "./chroma_db"):
        self.client = chromadb.PersistentClient(
            path=persist_path,
            settings=Settings(anonymized_telemetry=False),
        )
        self.collection = self.client.get_or_create_collection("qms_docs")

    async def add_chunks(self, chunks: list[DocumentChunk]) -> None:
        """批量写入，带来源元数据"""
        if not chunks:
            return
        self.collection.add(
            documents=[c.text for c in chunks],
            metadatas=[
                {
                    "filename": c.metadata.get("filename"),
                    "page": c.metadata.get("page"),
                    "level": c.metadata.get("level"),
                }
                for c in chunks
            ],
            ids=[c.chunk_id for c in chunks],
        )

    async def search(self, query: str, top_k: int = 5) -> list[DocumentChunk]:
        """检索并返回带来源标注的 chunks"""
        res = self.collection.query(query_texts=[query], n_results=top_k)
        results = []
        for doc, meta, cid in zip(res["documents"][0], res["metadatas"][0], res["ids"][0]):
            source = f"[来源：{meta['filename']}, 第{meta['page']}页]"
            results.append(
                DocumentChunk(
                    chunk_id=cid,
                    text=doc,
                    metadata={**meta, "source": source},
                )
            )
        return results