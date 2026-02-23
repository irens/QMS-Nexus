"""
根据 MIME 类型路由到对应解析引擎，零硬编码。
"""
from typing import Dict, Any, Optional
from pathlib import Path
import logging

from core.models import Chunk

log = logging.getLogger(__name__)


class BaseParserAdapter:
    """解析器抽象基类。"""

    async def parse(self, file_path: str, **options) -> list[Chunk]:
        raise NotImplementedError


class PDFParserAdapter(BaseParserAdapter):
    """PDF 解析器 - 使用 PyMuPDF (fitz)"""

    async def parse(self, file_path: str, **options) -> list[Chunk]:
        import fitz  # PyMuPDF
        import asyncio

        chunks = []
        path = Path(file_path)

        # 在线程池中执行同步的 PDF 解析
        loop = asyncio.get_event_loop()
        doc = await loop.run_in_executor(None, fitz.open, str(path))

        try:
            for page_num in range(len(doc)):
                page = doc[page_num]
                # 提取文本
                text = page.get_text()
                if text.strip():
                    chunks.append(Chunk(
                        text=text.strip(),
                        page=page_num + 1,
                        metadata={
                            "filename": path.name,
                            "page": page_num + 1,
                            "total_pages": len(doc)
                        }
                    ))
        finally:
            doc.close()

        log.info(f"[PDFParser] 解析完成: {path.name}, 共 {len(chunks)} 页有内容")
        return chunks


class WordParserAdapter(BaseParserAdapter):
    """Word 文档解析器 - 使用 python-docx"""

    async def parse(self, file_path: str, **options) -> list[Chunk]:
        import docx
        import asyncio

        path = Path(file_path)
        loop = asyncio.get_event_loop()
        doc = await loop.run_in_executor(None, docx.Document, str(path))

        chunks = []
        full_text = []

        for para in doc.paragraphs:
            if para.text.strip():
                full_text.append(para.text.strip())

        # 将文档内容分段
        text = "\n".join(full_text)
        if text:
            # 按段落分割成 chunks
            paragraphs = [p for p in text.split("\n") if p.strip()]
            for i, para in enumerate(paragraphs):
                chunks.append(Chunk(
                    text=para,
                    page=i + 1,  # 用段落号代替页码
                    metadata={
                        "filename": path.name,
                        "paragraph": i + 1,
                        "total_paragraphs": len(paragraphs)
                    }
                ))

        log.info(f"[WordParser] 解析完成: {path.name}, 共 {len(chunks)} 段")
        return chunks


class ExcelParserAdapter(BaseParserAdapter):
    """Excel 解析器 - 使用 openpyxl，表格转 Markdown"""

    async def parse(self, file_path: str, **options) -> list[Chunk]:
        import openpyxl
        import asyncio

        path = Path(file_path)
        loop = asyncio.get_event_loop()
        wb = await loop.run_in_executor(None, openpyxl.load_workbook, str(path))

        chunks = []
        table_as_markdown = options.get("table_as_markdown", True)

        try:
            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]

                if table_as_markdown:
                    # 转换为 Markdown 表格
                    rows = []
                    for row in sheet.iter_rows():
                        row_data = [str(cell.value or "") for cell in row]
                        rows.append("| " + " | ".join(row_data) + " |")

                    if len(rows) >= 2:  # 至少要有表头和一行数据
                        # 添加分隔符
                        header = rows[0]
                        col_count = len(rows[0].split("|")) - 2
                        separator = "|" + "|".join([" --- " for _ in range(col_count)]) + "|"
                        rows.insert(1, separator)

                        markdown_table = "\n".join(rows)
                        chunks.append(Chunk(
                            text=f"Sheet: {sheet_name}",
                            table=markdown_table,
                            metadata={
                                "filename": path.name,
                                "sheet": sheet_name,
                                "type": "excel_table"
                            }
                        ))
                else:
                    # 纯文本模式
                    texts = []
                    for row in sheet.iter_rows():
                        row_text = " ".join([str(cell.value or "") for cell in row])
                        if row_text.strip():
                            texts.append(row_text)

                    if texts:
                        chunks.append(Chunk(
                            text="\n".join(texts),
                            metadata={
                                "filename": path.name,
                                "sheet": sheet_name,
                                "type": "excel_text"
                            }
                        ))
        finally:
            wb.close()

        log.info(f"[ExcelParser] 解析完成: {path.name}, 共 {len(chunks)} 个 sheet")
        return chunks


class PPTParserAdapter(BaseParserAdapter):
    """PPT 解析器 - 使用 python-pptx"""

    async def parse(self, file_path: str, **options) -> list[Chunk]:
        from pptx import Presentation
        import asyncio

        path = Path(file_path)
        loop = asyncio.get_event_loop()
        prs = await loop.run_in_executor(None, Presentation, str(path))

        chunks = []

        for slide_num, slide in enumerate(prs.slides, 1):
            slide_texts = []
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_texts.append(shape.text.strip())

            if slide_texts:
                chunks.append(Chunk(
                    text="\n".join(slide_texts),
                    page=slide_num,
                    metadata={
                        "filename": path.name,
                        "slide": slide_num,
                        "total_slides": len(prs.slides)
                    }
                ))

        log.info(f"[PPTParser] 解析完成: {path.name}, 共 {len(chunks)} 页")
        return chunks


# -----------------------
# 路由表：MIME → 适配器类名
# -----------------------
ROUTER: Dict[str, str] = {
    # PDF
    "application/pdf": "PDFParserAdapter",
    # Word
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "WordParserAdapter",
    "application/msword": "WordParserAdapter",
    # Excel
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "ExcelParserAdapter",
    "application/vnd.ms-excel": "ExcelParserAdapter",
    # PPT
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": "PPTParserAdapter",
    "application/vnd.ms-powerpoint": "PPTParserAdapter",
}


def get_parser(mime: str) -> BaseParserAdapter:
    """工厂函数：根据 MIME 返回解析器实例。"""
    cls_name = ROUTER.get(mime)
    if not cls_name:
        # 尝试根据文件扩展名判断
        log.warning(f"未知的 MIME 类型: {mime}，尝试使用通用解析")
        raise ValueError(f"不支持的 MIME 类型: {mime}")

    # 动态导入当前模块
    module = __import__(__name__, fromlist=[cls_name])
    cls = getattr(module, cls_name)
    return cls()
