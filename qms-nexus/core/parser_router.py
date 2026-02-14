"""
根据 MIME 类型路由到对应解析引擎，零硬编码。
"""
from typing import Dict, Any, Optional
from core.models import Chunk

class BaseParserAdapter:
    """解析器抽象基类。"""

    async def parse(self, file_path: str, **options) -> list[Chunk]:
        raise NotImplementedError

class MinerUAdapter(BaseParserAdapter):
    """MinerU PDF 解析器。"""

    async def parse(self, file_path: str, **options) -> list[Chunk]:
        # 伪代码：实际调用 MinerU SDK
        # from mineru import parse_pdf
        # pages = parse_pdf(file_path)
        # return [Chunk(text=p.text, page=p.page) for p in pages]
        return [
            Chunk(text="质量风险管理流程示例", page=1, metadata={"filename": file_path}),
            Chunk(text="客户投诉处理规范", page=2, metadata={"filename": file_path}),
        ]

class UnstructuredAdapter(BaseParserAdapter):
    """Unstructured Excel 解析器。"""

    async def parse(self, file_path: str, **options) -> list[Chunk]:
        # 伪代码：实际调用 unstructured
        # from unstructured import partition_xlsx
        # elements = partition_xlsx(file_path)
        # table_md = elements_to_markdown_table(elements)
        table_as_markdown = options.get("table_as_markdown", False)
        return [
            Chunk(
                text="检验规范表格",
                table="| 项目 | 要求 |\n| ---- | ---- |\n| 外观 | 无瑕疵 |" if table_as_markdown else None,
                metadata={"filename": file_path},
            )
        ]

# -----------------------
# 路由表：MIME → 适配器类名
# -----------------------
ROUTER: Dict[str, str] = {
    "application/pdf": "MinerUAdapter",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "UnstructuredAdapter",
    "application/vnd.ms-excel": "UnstructuredAdapter",
}

def get_parser(mime: str) -> BaseParserAdapter:
    """工厂函数：根据 MIME 返回解析器实例。"""
    cls_name = ROUTER.get(mime)
    if not cls_name:
        raise ValueError(f"不支持的 MIME 类型: {mime}")
    # 动态导入当前模块
    module = __import__(__name__, fromlist=[cls_name])
    cls = getattr(module, cls_name)
    return cls()