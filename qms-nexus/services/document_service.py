"""
文档解析编排 Service
调用 arq 投递异步任务，后台 worker 完成解析与入库
"""
import asyncio
from pathlib import Path

from arq import create_pool
from arq.connections import RedisSettings
from core.config import settings
from core.task_store import set_task


class DocumentService:
    """投递异步任务，后台 worker 完成解析与入库"""

    async def process(
        self,
        task_id: str,
        file_path: Path,
        mime: str,
        collection: str = "qms_docs"
    ) -> None:
        """投递任务到 Redis 队列，立即返回"""
        set_task(task_id, {
            "status": "Processing",
            "filename": file_path.name,
            "collection": collection
        })
        pool = await create_pool(RedisSettings.from_dsn(settings.REDIS_URL))
        await pool.enqueue_job(
            "parse_doc_task",
            str(file_path),
            task_id,
            mime,
            collection,
            _queue_name=settings.ARQ_QUEUE_NAME,
        )
        await pool.close()
