"""
RAG 业务 Service 层
封装检索 + 大模型调用，禁止在 API 层直接写逻辑
"""
import time
from typing import Optional, List, Dict, Any

from core.llm import LLMClient
from core.vectordb import VectorDBClient
from services.prompt_service import PromptService
from core.logger import get_logger
from core.cache import CacheClient
from core.correction_service import correction_service

logger = get_logger(__name__)


class RAGService:
    def __init__(self):
        self.db = VectorDBClient()
        self.llm = LLMClient()
        self.prompt = PromptService()
        self.cache = CacheClient()

    async def answer(
        self,
        question: str,
        collection: str = "qms_docs",
        skip_correction: bool = False
    ) -> tuple[str, list[str], Dict[str, Any]]:
        """
        检索 → 生成答案
        
        流程:
        1. 优先查询修正库
        2. 如无修正记录，执行向量检索
        3. 生成答案
        
        Args:
            question: 问题
            collection: 知识库名称
            skip_correction: 是否跳过修正库查询
            
        Returns:
            (answer, sources, metadata)
            metadata 包含 is_corrected 标记是否来自修正库
        """
        t0 = time.time()
        logger.info(
            f"开始问答",
            extra={"user": "anonymous", "question": question, "collection": collection}
        )
        
        # 检查缓存
        cache_key = f"q:{question.strip()}:collection:{collection}"
        cached = self.cache.get(cache_key)
        if cached:
            logger.info("缓存命中", extra={"user": "anonymous", "cost": time.time() - t0})
            return cached["answer"], cached["sources"], cached.get("metadata", {})

        # 1. 优先查询修正库
        if not skip_correction:
            correction = correction_service.find_correction(question)
            if correction:
                answer = correction["correct_answer"]
                source = "[来源：人工修正答案"
                if correction.get("source_doc"):
                    source += f" - {correction['source_doc']}"
                    if correction.get("page_number"):
                        source += f", 第{correction['page_number']}页"
                source += "]"
                
                metadata = {
                    "is_corrected": True,
                    "correction_id": correction["id"],
                    "original_answer": correction.get("original_answer"),
                    "source_doc": correction.get("source_doc"),
                    "page_number": correction.get("page_number"),
                }
                
                # 写入缓存
                self.cache.set(cache_key, {"answer": answer, "sources": [source], "metadata": metadata})
                
                logger.info(
                    "修正库命中",
                    extra={
                        "user": "anonymous",
                        "correction_id": correction["id"],
                        "cost": time.time() - t0
                    }
                )
                return answer, [source], metadata

        # 2. 执行向量检索
        results = await self.db.similarity_search(question, top_k=5, collection=collection)
        if not results:
            logger.info("无结果", extra={"user": "anonymous", "cost": time.time() - t0})
            return "知识库中暂无相关记录", [], {"is_corrected": False}

        context = "\n".join(r.text for r in results)
        sources = [r.source for r in results]

        # 3. 生成答案
        system = self.prompt.render({"context": context, "question": question})
        answer = await self.llm.chat(system=system, user="请回答上述问题。")
        
        metadata = {"is_corrected": False}
        
        # 写入缓存
        self.cache.set(cache_key, {"answer": answer, "sources": sources, "metadata": metadata})
        
        logger.info("完成问答", extra={"user": "anonymous", "cost": time.time() - t0})
        return answer, sources, metadata

    async def answer_with_feedback(
        self,
        question: str,
        correct_answer: Optional[str] = None,
        collection: str = "qms_docs",
        save_correction: bool = False
    ) -> tuple[str, list[str], Dict[str, Any]]:
        """
        问答并可选保存修正
        
        Args:
            question: 问题
            correct_answer: 如果提供，直接作为正确答案返回并存入修正库
            collection: 知识库名称
            save_correction: 是否保存到修正库
        """
        if correct_answer and save_correction:
            # 保存修正并返回
            correction_id = correction_service.add_correction(
                question=question,
                correct_answer=correct_answer,
                source_doc="用户修正"
            )
            source = "[来源：人工修正答案 - 用户修正]"
            metadata = {
                "is_corrected": True,
                "correction_id": correction_id,
                "saved": True
            }
            return correct_answer, [source], metadata
        
        # 正常流程
        return await self.answer(question, collection=collection)
