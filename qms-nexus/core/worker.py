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

log = logging.getLogger(__name__)


async def parse_doc_task(ctx: Dict[str, Any], file_path: str, task_id: str, mime: str = None) -> str:
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
        chunks = await asyncio.to_thread(parser.parse, str(path))
        if not chunks:
            log.warning(f"[task {task_id}] 未提取到任何文本")
            return "completed"  # 空文件也算完成

        db = VectorDBClient()
        await db.add_texts(
            texts=[c.text for c in chunks],
            metadatas=[
                {
                    "source": f"{path.name}, 第{c.page}",
                    "tags": [],
                }
                for c in chunks
            ],
        )
        log.info(f"[task {task_id}] 写入 {len(chunks)} 条向量，完成")
        return "completed"
    except Exception as e:
        log.exception(f"[task {task_id}] 解析失败: {e}")
        return "failed"


# arq worker 启动配置
class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.REDIS_URL)
    functions = [parse_doc_task]
    # 可根据需要添加定时任务
    # cron_jobs = [cron(coro, hour=1)]