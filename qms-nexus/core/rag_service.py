"""
RAG 业务 Service 层
封装检索 + 大模型调用，禁止在 API 层直接写逻辑
"""
from core.llm import LLMClient
from core.vectordb import VectorDBClient
from services.prompt_service import PromptService


class RAGService:
    def __init__(self):
        self.db = VectorDBClient()
        self.llm = LLMClient()
        self.prompt = PromptService()

    async def answer(self, question: str) -> tuple[str, list[str]]:
        """检索 → 生成答案，无结果返回固定文案"""
        results = await self.db.similarity_search(question, top_k=5)
        if not results:
            return "知识库中暂无相关记录", []

        context = "\n".join(r.text for r in results)
        sources = [r.source for r in results]

        system = self.prompt.render({"context": context, "question": question})
        answer = await self.llm.chat(system=system, user="请回答上述问题。")
        return answer, sources