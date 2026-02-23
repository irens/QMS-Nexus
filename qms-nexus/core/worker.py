"""
arq Worker 任务定义
"""
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict

from arq import create_pool, cron
from arq.connections import RedisSettings

from .parser_router import get_parser
from .vectordb import VectorDBClient
from .config import settings
from .task_store import update_task_status

log = logging.getLogger(__name__)


async def parse_doc_task(ctx: Dict[str, Any], file_path: str, task_id: str, mime: str = None, collection: str = "qms_docs") -> str:
    """
    异步解析文档并写入向量库。
    成功返回 'completed'，失败返回 'failed'。
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
        await db.upsert_chunks(chunks, collection=collection)
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
