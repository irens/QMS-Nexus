"""
补齐 parser_router.py 缺失分支（未实现异常）
运行：pytest tests/unit/test_parser_router_full.py -q
"""
import pytest
from core.parser_router import BaseParserAdapter, get_parser

class DummyParser(BaseParserAdapter):
    pass  # 不实现 parse，触发 NotImplementedError

def test_base_parser_not_implemented():
    """覆盖基类未实现异常"""
    p = DummyParser()
    with pytest.raises(NotImplementedError):
        p.parse("dummy.pdf")

def test_unsupported_mime():
    """覆盖不支持的 MIME 异常"""
    with pytest.raises(ValueError, match="不支持的 MIME 类型"):
        get_parser("text/plain")