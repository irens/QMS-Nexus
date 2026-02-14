"""
文档解析统一入口
支持 MinerU 或 Unstructured，Excel 先转 Markdown
"""
import asyncio
from pathlib import Path
from typing import Literal, TypedDict

from core.models import DocumentChunk


class ParseTask(TypedDict):
    file_path: str
    task_id: str


class ParseResult(TypedDict):
    task_id: str
    status: Literal["Pending", "Processing", "Completed", "Failed"]
    chunks: list[DocumentChunk]
    message: str


class DocParser:
    """异步文档解析器，支持回调状态"""

    async def parse(self, task: ParseTask) -> ParseResult:
        """入口：根据后缀路由到具体解析器"""
        path = Path(task["file_path"])
        if path.suffix.lower() in (".xlsx", ".xls"):
            return await self._parse_excel(task)
        return await self._parse_unstructured(task)

    async def _parse_excel(self, task: ParseTask) -> ParseResult:
        """Excel → Markdown → chunks"""
        await asyncio.sleep(0.1)  # 模拟异步
        # TODO: 集成 MinerU 或 openpyxl → Markdown
        return ParseResult(
            task_id=task["task_id"],
            status="Completed",
            chunks=[],
            message="Excel→Markdown 待实现",
        )

    async def _parse_unstructured(self, task: ParseTask) -> ParseResult:
        """其他格式走 Unstructured"""
        await asyncio.sleep(0.1)
        # TODO: 集成 unstructured
        return ParseResult(
            task_id=task["task_id"],
            status="Completed",
            chunks=[],
            message="Unstructured 待实现",
        )