"""
单元测试：路由表 & 工厂函数。
运行：pytest tests/unit/test_parser_router.py -q
"""
import pytest
from core.parser_router import get_parser, MinerUAdapter, UnstructuredAdapter

def test_get_parser_pdf():
    p = get_parser("application/pdf")
    assert isinstance(p, MinerUAdapter)

def test_get_parser_excel():
    p = get_parser("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    assert isinstance(p, UnstructuredAdapter)

def test_unsupported_mime():
    with pytest.raises(ValueError):
        get_parser("text/plain")