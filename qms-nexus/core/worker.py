"""
arq Worker 任务定义
"""
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from arq import create_pool, cron
from arq.connections import RedisSettings

from .parser_router import get_parser
from .vectordb import VectorDBClient
from .config import settings
from .task_store import update_task_status
from .document_version_store import document_version_store

log = logging.getLogger(__name__)


async def parse_doc_task(
    ctx: Dict[str, Any],
    file_path: str,
    task_id: str,
    mime: str = None,
    collection: str = "qms_docs",
    version_id: Optional[str] = None,
) -> str:
    """
    异步解析文档并写入向量库。
    成功返回 'completed'，失败返回 'failed'。

    Args:
        ctx: arq上下文
        file_path: 文件路径
        task_id: 任务ID
        mime: MIME类型
        collection: 知识库名称
        version_id: 文档版本ID（可选），如果提供则会将版本信息写入向量库
    """
    try:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(file_path)

        log.info(f"[task {task_id}] 开始解析 {path.name}")
        parser = get_parser(mime or "application/pdf")
        chunks = await parser.parse(str(path))
        if not chunks:
            log.warning(f"[task {task_id}] 未提取到任何文本")
            update_task_status(task_id, "Completed")
            return "completed"

        db = VectorDBClient()
        for c in chunks:
            c.metadata["filename"] = path.name
            c.metadata["collection"] = collection

        # 构建版本元数据
        version_metadata = None
        if version_id:
            try:
                version_info = await document_version_store.get_version_by_id(version_id)
                if version_info:
                    version_metadata = {
                        "version_id": version_id,
                        "version_number": version_info.version_number,
                        "version_label": version_info.version_label,
                        "status": version_info.status,
                        "effective_date": version_info.effective_date.isoformat() if version_info.effective_date else None,
                        "is_latest": version_info.is_latest,
                    }
                    log.info(f"[task {task_id}] 版本信息: {version_info.version_label} (status={version_info.status})")
            except Exception as e:
                log.warning(f"[task {task_id}] 获取版本信息失败: {e}")

        await db.upsert_chunks(chunks, collection=collection, version_metadata=version_metadata)
        log.info(f"[task {task_id}] 写入 {len(chunks)} 条向量，完成")
        update_task_status(task_id, "Completed", chunks_count=len(chunks))
        return "completed"
    except Exception as e:
        log.exception(f"[task {task_id}] 解析失败: {e}")
        update_task_status(task_id, "Failed", error=str(e))
        return "failed"


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    functions = [parse_doc_task]
    queue_name = settings.ARQ_QUEUE_NAME
    # 增加健康检查间隔，保持连接活跃
    health_check_interval = 30
    # 任务超时时间（秒）
    job_timeout = 300
    # 最大并发任务数
    max_jobs = 5
