"""
单元测试：ChromaDB 增删改查 & 相似检索。
运行：pytest tests/unit/test_vectordb.py -q
"""
import asyncio
import pytest
from core.vectordb import VectorDBClient
from core.models import Chunk, EmbeddingConfig

@pytest.fixture
def vdb():
    return VectorDBClient(persist_dir="./test_chroma", embedding_config=EmbeddingConfig())

@pytest.mark.asyncio
async def test_upsert_and_search(vdb: VectorDBClient):
    chunks = [
        Chunk(text="质量风险管理流程", page=1, metadata={"filename": "demo.pdf", "tags": ["设计文档"]}),
        Chunk(text="客户投诉处理规范", page=2, metadata={"filename": "demo.pdf", "tags": ["客户投诉"]}),
    ]
    ids = await vdb.upsert_chunks(chunks)
    assert len(ids) == 2

    results = await vdb.similarity_search("质量风险", top_k=1)
    assert len(results) == 1
    assert "质量" in results[0].text

@pytest.mark.asyncio
async def test_filter_by_tags(vdb: VectorDBClient):
    # 单独写入带标签数据
    await vdb.upsert_chunks([
        Chunk(text="客户投诉处理规范", page=1, metadata={"filename": "tagged.pdf", "tags": ["客户投诉"]})
    ])
    results = await vdb.similarity_search("投诉", filter_tags=["客户投诉"])
    assert len(results) >= 1
    assert "客户投诉" in results[0].tags

@pytest.mark.asyncio
async def test_delete_by_filename(vdb: VectorDBClient):
    n = await vdb.delete_by_filename("demo.pdf")
    assert n == 2

@pytest.mark.asyncio
async def test_ping(vdb: VectorDBClient):
    assert await vdb.ping() is True