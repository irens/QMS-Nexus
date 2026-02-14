"""
RAG 业务 Service 层
封装检索 + 大模型调用，禁止在 API 层直接写逻辑
"""
import time
from core.llm import LLMClient
from core.vectordb import VectorDBClient
from services.prompt_service import PromptService
from core.logger import get_logger
from core.cache import CacheClient

logger = get_logger(__name__)


class RAGService:
    def __init__(self):
        self.db = VectorDBClient()
        self.llm = LLMClient()
        self.prompt = PromptService()
        self.cache = CacheClient()

    async def answer(self, question: str) -> tuple[str, list[str]]:
        """检索 → 生成答案，无结果返回固定文案；缓存 5 min"""
        t0 = time.time()
        logger.info(f"开始问答", extra={"user": "anonymous", "question": question})
        # 缓存 key
        cache_key = f"q:{question.strip()}"
        cached = self.cache.get(cache_key)
        if cached:
            logger.info("缓存命中", extra={"user": "anonymous", "cost": time.time() - t0})
            return cached["answer"], cached["sources"]

        results = await self.db.similarity_search(question, top_k=5)
        if not results:
            logger.info("无结果", extra={"user": "anonymous", "cost": time.time() - t0})
            return "知识库中暂无相关记录", []

        context = "\n".join(r.text for r in results)
        sources = [r.source for r in results]

        system = self.prompt.render({"context": context, "question": question})
        answer = await self.llm.chat(system=system, user="请回答上述问题。")
        # 写入缓存
        self.cache.set(cache_key, {"answer": answer, "sources": sources})
        logger.info("完成问答", extra={"user": "anonymous", "cost": time.time() - t0})
        return answer, sources