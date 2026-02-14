"""
文档解析编排 Service
调用 parser_router + 写向量库 + 更新任务状态
"""
import asyncio
from pathlib import Path
from typing import Dict, Optional

from core.parser_router import get_parser
from core.vectordb import VectorDBClient
from core.models import Chunk

# 内存级任务存储（阶段三换 Redis）
tasks: Dict[str, dict] = {}


class DocumentService:
    """异步解析并入库"""

    def __init__(self):
        self.vdb = VectorDBClient()

    async def process(self, task_id: str, file_path: Path, mime: str) -> None:
        """后台解析 → 写入向量库 → 更新任务状态"""
        tasks[task_id] = {"status": "Processing", "filename": file_path.name}
        try:
            parser = get_parser(mime)
            chunks = await parser.parse(str(file_path))
            await self.vdb.upsert_chunks(chunks)
            tasks[task_id]["status"] = "Completed"
        except Exception as e:
            tasks[task_id]["status"] = "Failed"
            tasks[task_id]["error"] = str(e)

    def get_status(self, task_id: str) -> Optional[dict]:
        return tasks.get(task_id)