"""
RAG 业务 Service 层
封装检索 + 大模型调用，禁止在 API 层直接写逻辑
"""
from core.llm import llm_call
from database.chromadb_service import ChromaService


class RAGService:
    def __init__(self):
        self.db = ChromaService()

    async def answer(self, question: str) -> tuple[str, list[str]]:
        """检索 → 生成答案，无结果返回固定文案"""
        chunks = await self.db.search(question, top_k=5)
        if not chunks:
            return "知识库中暂无相关记录", []

        context = "\n".join(c.text for c in chunks)
        sources = [c.metadata["source"] for c in chunks]

        prompt = f"Context:\n{context}\n\nQuestion: {question}\nAnswer:"
        answer = await llm_call(prompt)
        return answer, sources