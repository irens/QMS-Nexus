"""
单元测试：core/parser_router.py MIME 路由
"""
import pytest
from core.parser_router import get_parser, MinerUAdapter, UnstructuredAdapter


@pytest.mark.asyncio
async def test_get_parser_pdf():
    """PDF → MinerUAdapter"""
    parser = get_parser("application/pdf")
    assert isinstance(parser, MinerUAdapter)
    chunks = await parser.parse("dummy.pdf")
    assert len(chunks) == 2
    assert "质量风险管理流程示例" in chunks[0].text


@pytest.mark.asyncio
async def test_get_parser_excel():
    """Excel → UnstructuredAdapter，默认带 Markdown 表格"""
    parser = get_parser("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    assert isinstance(parser, UnstructuredAdapter)
    chunks = await parser.parse("dummy.xlsx", table_as_markdown=True)
    assert len(chunks) == 1
    assert "| 项目 | 要求 |" in chunks[0].table


@pytest.mark.asyncio
async def test_get_parser_unsupported():
    """不支持的 MIME 抛错。"""
    with pytest.raises(ValueError, match="不支持的 MIME 类型"):
        get_parser("text/plain")