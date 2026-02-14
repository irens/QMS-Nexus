"""
快速单元测试：验证基础模型字段合法性。
运行：pytest tests/unit/test_models.py -q
"""
import pytest
from core.models import CompanyConfig, GlobalConfig, Chunk, Document, SearchRequest

def test_company_config():
    cc = CompanyConfig(name="ACME", product="输液器", industry="医疗器械")
    assert cc.name == "ACME"

def test_chunk_defaults():
    c = Chunk(text="hello")
    assert c.page is None
    assert c.metadata == {}

def test_search_request_validation():
    with pytest.raises(ValueError):
        SearchRequest(q="")  # min_length=1

@pytest.mark.asyncio
async def test_document_with_chunks():
    d = Document(filename="demo.pdf", mime="application/pdf")
    d.chunks.append(Chunk(text="chunk1", page=1))
    assert len(d.chunks) == 1
    assert d.chunks[0].page == 1