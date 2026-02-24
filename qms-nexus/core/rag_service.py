"""
RAG 业务 Service 层
封装检索 + 大模型调用，禁止在 API 层直接写逻辑
支持文档版本管理功能
"""
import time
from datetime import datetime
from typing import Optional, List, Dict, Any

from core.llm import LLMClient
from core.vectordb import VectorDBClient
from services.prompt_service import PromptService
from core.logger import get_logger
from core.cache import CacheClient
from core.correction_service import correction_service, calculate_similarity
from core.config import settings
from core.document_version_store import document_version_store, VersionStatus

logger = get_logger(__name__)


class RAGService:
    def __init__(self):
        self.db = VectorDBClient()
        self.llm = LLMClient()
        self.prompt = PromptService()
        self.cache = CacheClient()

    async def search(
        self,
        query: str,
        kb_id: str = "default",
        version_strategy: str = "latest_effective",
        specific_date: Optional[datetime] = None,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        搜索文档，支持版本策略

        Args:
            query: 搜索查询
            kb_id: 知识库ID
            version_strategy: 版本策略
                - "latest_effective": 只搜索最新生效版本（默认）
                - "specific_date": 搜索指定日期生效的版本
                - "all_versions": 搜索所有版本（用于对比）
            specific_date: 指定日期，用于 specific_date 策略
            top_k: 返回结果数量
            filters: 额外的过滤条件

        Returns:
            搜索结果列表，包含版本信息
        """
        # 构建过滤条件
        version_filter = {"kb_id": kb_id}

        if version_strategy == "latest_effective":
            # 只搜索最新且生效的版本
            version_filter["is_latest"] = True
            version_filter["status"] = VersionStatus.EFFECTIVE.value

        elif version_strategy == "specific_date":
            # 搜索指定日期生效的版本
            if specific_date:
                effective_versions = await self._get_effective_versions_at_date(
                    kb_id, specific_date
                )
                if effective_versions:
                    # ChromaDB 不支持 $in 操作符，需要分别查询然后合并
                    all_results = []
                    for version_id in effective_versions:
                        vf = {"version_id": version_id}
                        if filters:
                            vf.update(filters)
                        results = await self.db.similarity_search(
                            query=query,
                            top_k=top_k,
                            collection=kb_id,
                            version_filter=vf,
                        )
                        all_results.extend(results)
                    # 按分数排序并截取 top_k
                    all_results.sort(key=lambda x: x.score, reverse=True)
                    return self._format_search_results(all_results[:top_k])
                else:
                    return []

        elif version_strategy == "all_versions":
            # 搜索所有版本，不过滤
            pass

        # 应用额外的过滤条件
        if filters:
            version_filter.update(filters)

        # 执行搜索
        results = await self.db.similarity_search(
            query=query,
            top_k=top_k,
            collection=kb_id,
            version_filter=version_filter if version_filter else None,
        )

        return self._format_search_results(results)

    def _format_search_results(self, results: List[Any]) -> List[Dict[str, Any]]:
        """格式化搜索结果，添加版本信息"""
        formatted = []
        for r in results:
            meta = r.metadata or {}
            formatted.append({
                "text": r.text,
                "score": r.score,
                "source": r.source,
                "filename": meta.get("filename"),
                "page": meta.get("page"),
                "version_id": meta.get("version_id"),
                "version_number": meta.get("version_number"),
                "version_label": meta.get("version_label"),
                "status": meta.get("status"),
                "effective_date": meta.get("effective_date"),
                "is_latest": meta.get("is_latest"),
                "warning": self._get_version_warning(meta),
            })
        return formatted

    def _get_version_warning(self, metadata: Dict[str, Any]) -> Optional[str]:
        """获取版本警告信息"""
        status = metadata.get("status")
        is_latest = metadata.get("is_latest")
        version_label = metadata.get("version_label")

        if status == VersionStatus.OBSOLETE.value:
            return "该版本已作废，建议查看最新版本"
        elif not is_latest and version_label:
            return f"该文档已有新版本"
        return None

    async def _get_effective_versions_at_date(
        self,
        kb_id: str,
        date: datetime,
    ) -> List[str]:
        """获取指定日期生效的所有版本ID"""
        # 这里需要查询数据库获取该日期生效的版本ID列表
        # 简化实现：获取所有生效中的版本，然后检查生效日期
        # 实际实现可能需要更复杂的查询逻辑
        try:
            # 获取所有文档的最新版本
            # 这是一个简化实现，实际可能需要根据业务需求调整
            return []
        except Exception as e:
            logger.error(f"获取指定日期生效版本失败: {e}")
            return []

    async def answer(
        self,
        question: str,
        collection: str = "qms_docs",
        skip_correction: bool = False,
        version_strategy: str = "latest_effective",
        specific_date: Optional[datetime] = None,
        include_version_info: bool = True,
    ) -> tuple[str, list[str], Dict[str, Any]]:
        """
        检索 → 生成答案，支持版本管理

        流程:
        1. 优先查询修正库
        2. 如无修正记录，根据版本策略执行向量检索
        3. 生成答案

        Args:
            question: 问题
            collection: 知识库名称
            skip_correction: 是否跳过修正库查询
            version_strategy: 版本策略
                - "latest_effective": 只搜索最新生效版本（默认）
                - "specific_date": 搜索指定日期生效的版本
                - "all_versions": 搜索所有版本（用于对比）
            specific_date: 指定日期，用于 specific_date 策略
            include_version_info: 是否在答案中包含版本信息

        Returns:
            (answer, sources, metadata)
            metadata 包含 is_corrected 标记是否来自修正库，以及版本信息
        """
        t0 = time.time()
        logger.info(
            f"开始问答",
            extra={
                "user": "anonymous",
                "question": question,
                "collection": collection,
                "version_strategy": version_strategy,
            }
        )

        # 检查缓存（缓存键包含版本策略）
        cache_key = f"q:{question.strip()}:collection:{collection}:strategy:{version_strategy}"
        if specific_date:
            cache_key += f":date:{specific_date.isoformat()}"
        cached = self.cache.get(cache_key)
        if cached:
            logger.info("缓存命中", extra={"user": "anonymous", "cost": time.time() - t0})
            return cached["answer"], cached["sources"], cached.get("metadata", {})

        # 1. 优先查询修正库（先精确匹配，再相似度匹配）
        if not skip_correction:
            correction = None
            similarity = 1.0

            # 1.1 先尝试精确匹配
            correction = correction_service.find_correction(question)

            # 1.2 精确匹配失败，尝试相似度匹配
            if not correction:
                correction, similarity = correction_service.find_correction_with_similarity(
                    question,
                    threshold=settings.CORRECTION_MATCH_THRESHOLD
                )

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
                    "similarity": similarity,
                }

                # 写入缓存
                self.cache.set(cache_key, {"answer": answer, "sources": [source], "metadata": metadata})

                logger.info(
                    "修正库命中",
                    extra={
                        "user": "anonymous",
                        "correction_id": correction["id"],
                        "similarity": similarity,
                        "cost": time.time() - t0
                    }
                )
                return answer, [source], metadata

        # 2. 根据版本策略执行向量检索
        search_results = await self.search(
            query=question,
            kb_id=collection,
            version_strategy=version_strategy,
            specific_date=specific_date,
            top_k=5,
        )

        if not search_results:
            logger.info("无结果", extra={"user": "anonymous", "cost": time.time() - t0})
            return "知识库中暂无相关记录", [], {"is_corrected": False}

        # 构建上下文
        context = "\n".join(r["text"] for r in search_results)

        # 构建来源信息，包含版本信息
        sources = []
        version_sources = []
        for r in search_results:
            source_text = r["source"]
            sources.append(source_text)

            # 构建详细的来源信息
            version_info = {
                "document_name": r["filename"],
                "version_id": r.get("version_id"),
                "version_number": r.get("version_number"),
                "version_label": r.get("version_label"),
                "status": r.get("status"),
                "is_latest": r.get("is_latest"),
                "page": r.get("page"),
                "score": r.get("score"),
                "warning": r.get("warning"),
            }
            version_sources.append(version_info)

        # 3. 生成答案
        system = self._get_system_prompt(version_strategy)
        system = self.prompt.render({"context": context, "question": question, "system": system})
        chat_result = await self.llm.chat(system=system, user="请回答上述问题。")

        answer = chat_result.text
        metadata = {
            "is_corrected": False,
            "model_used": chat_result.model_used,
            "tokens_used": chat_result.tokens_used,
            "is_fallback": chat_result.is_fallback,
            "version_strategy": version_strategy,
            "sources": version_sources if include_version_info else None,
        }

        # 写入缓存
        self.cache.set(cache_key, {"answer": answer, "sources": sources, "metadata": metadata})

        logger.info(
            "完成问答",
            extra={
                "user": "anonymous",
                "cost": time.time() - t0,
                "model": chat_result.model_used,
                "tokens": chat_result.tokens_used,
                "version_strategy": version_strategy,
            }
        )
        return answer, sources, metadata

    def _get_system_prompt(self, version_strategy: str) -> str:
        """根据版本策略获取系统提示词"""
        base_prompt = "你是一个专业的医疗器械质量管理体系助手。"

        if version_strategy == "latest_effective":
            return base_prompt + "请基于最新生效的文档版本回答问题。"
        elif version_strategy == "specific_date":
            return base_prompt + "请基于指定日期生效的文档版本回答问题。"
        elif version_strategy == "all_versions":
            return base_prompt + "请基于所有文档版本回答问题，注意区分不同版本的差异。"
        return base_prompt

    def _chunks_to_text(self, chunks: List[Any]) -> str:
        """将chunks列表转换为文本"""
        if not chunks:
            return ""
        texts = []
        for chunk in chunks:
            if hasattr(chunk, 'text'):
                page_info = f"[第{chunk.metadata.get('page', '?')}页] " if hasattr(chunk, 'metadata') else ""
                texts.append(f"{page_info}{chunk.text}")
            elif isinstance(chunk, dict):
                page_info = f"[第{chunk.get('page', '?')}页] "
                texts.append(f"{page_info}{chunk.get('text', '')}")
        return "\n\n".join(texts)

    async def compare_versions_search(
        self,
        document_id: str,
        v1_id: str,
        v2_id: str,
        collection: str = "qms_docs",
    ) -> Dict[str, Any]:
        """
        对比两个版本的差异
        用于回答"新旧版本有什么区别"这类问题

        Args:
            document_id: 文档组ID
            v1_id: 版本1 ID（旧版本）
            v2_id: 版本2 ID（新版本）
            collection: 知识库名称

        Returns:
            版本对比结果，包含摘要、新增/删除/修改的部分
        """
        t0 = time.time()
        logger.info(
            f"开始版本对比",
            extra={
                "document_id": document_id,
                "v1_id": v1_id,
                "v2_id": v2_id,
            }
        )

        # 1. 获取两个版本的元数据
        v1_info = await document_version_store.get_version_by_id(v1_id)
        v2_info = await document_version_store.get_version_by_id(v2_id)

        if not v1_info or not v2_info:
            raise ValueError("版本不存在")

        # 2. 获取两个版本的所有chunks
        v1_chunks = await self.db.get_chunks_by_version(v1_id, collection=collection)
        v2_chunks = await self.db.get_chunks_by_version(v2_id, collection=collection)

        # 3. 使用LLM分析差异
        v1_content = self._chunks_to_text(v1_chunks)
        v2_content = self._chunks_to_text(v2_chunks)

        # 构建对比提示词
        compare_prompt = f"""请对比以下两个版本的文档内容，分析它们之间的差异。

【版本1: {v1_info.version_label}】
状态: {v1_info.status}
变更摘要: {v1_info.change_summary or '无'}

内容:
{v1_content[:8000]}  # 限制长度避免超出token限制

【版本2: {v2_info.version_label}】
状态: {v2_info.status}
变更摘要: {v2_info.change_summary or '无'}

内容:
{v2_content[:8000]}

请分析并提供以下信息（以JSON格式回复）:
{{
    "summary": "总体变更概述",
    "added_sections": ["新增的内容要点"],
    "removed_sections": ["删除的内容要点"],
    "modified_sections": ["修改的内容要点"],
    "key_changes": ["关键变更点"]
}}
"""

        try:
            chat_result = await self.llm.chat(
                system="你是一个专业的文档对比分析助手。请仔细对比两个版本的文档内容，识别新增、删除和修改的部分。",
                user=compare_prompt
            )

            # 解析LLM返回的结果
            answer = chat_result.text

            # 尝试从回答中提取结构化数据
            import json
            import re

            # 尝试提取JSON部分
            json_match = re.search(r'\{.*\}', answer, re.DOTALL)
            if json_match:
                try:
                    analysis = json.loads(json_match.group())
                except json.JSONDecodeError:
                    # 如果JSON解析失败，使用文本内容构建结构
                    analysis = {
                        "summary": answer[:500],
                        "added_sections": [],
                        "removed_sections": [],
                        "modified_sections": [],
                        "key_changes": [],
                    }
            else:
                analysis = {
                    "summary": answer[:500],
                    "added_sections": [],
                    "removed_sections": [],
                    "modified_sections": [],
                    "key_changes": [],
                }

            # 构建返回结果
            result = {
                "summary": analysis.get("summary", "版本对比分析"),
                "added_sections": analysis.get("added_sections", []),
                "removed_sections": analysis.get("removed_sections", []),
                "modified_sections": analysis.get("modified_sections", []),
                "key_changes": analysis.get("key_changes", []),
                "v1_info": {
                    "version_id": v1_id,
                    "version_label": v1_info.version_label,
                    "version_number": v1_info.version_number,
                    "status": v1_info.status,
                    "change_summary": v1_info.change_summary,
                },
                "v2_info": {
                    "version_id": v2_id,
                    "version_label": v2_info.version_label,
                    "version_number": v2_info.version_number,
                    "status": v2_info.status,
                    "change_summary": v2_info.change_summary,
                },
                "stats": {
                    "v1_chunks": len(v1_chunks),
                    "v2_chunks": len(v2_chunks),
                },
            }

            logger.info(
                "版本对比完成",
                extra={
                    "document_id": document_id,
                    "v1_id": v1_id,
                    "v2_id": v2_id,
                    "cost": time.time() - t0,
                }
            )

            return result

        except Exception as e:
            logger.error(f"版本对比分析失败: {e}")
            # 返回基础对比信息
            return {
                "summary": f"版本 {v1_info.version_label} 与 {v2_info.version_label} 的对比",
                "added_sections": [],
                "removed_sections": [],
                "modified_sections": [],
                "key_changes": [v2_info.change_summary or "无详细变更说明"],
                "v1_info": {
                    "version_id": v1_id,
                    "version_label": v1_info.version_label,
                    "version_number": v1_info.version_number,
                    "status": v1_info.status,
                },
                "v2_info": {
                    "version_id": v2_id,
                    "version_label": v2_info.version_label,
                    "version_number": v2_info.version_number,
                    "status": v2_info.status,
                },
                "stats": {
                    "v1_chunks": len(v1_chunks),
                    "v2_chunks": len(v2_chunks),
                },
                "error": str(e),
            }

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
