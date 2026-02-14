"""
单元测试：core/vectordb.py 写入→检索→删除全流程
"""
import asyncio
import pytest
import pytest_asyncio

from core.models import Chunk
from core.vectordb import VectorDBClient


@pytest_asyncio.fixture
async def vdb():
    """内存级临时客户端，测试后自动清理。"""
    import uuid
    coll_name = f"test_{uuid.uuid4().hex}"
    client = VectorDBClient(persist_dir=":memory:")
    yield client, coll_name
    # 内存模式无需手动清理


@pytest.mark.asyncio
async def test_upsert_and_search(vdb):
    client, coll_name = vdb
    """写入 3 条 chunks → 检索 → 断言来源标注。"""
    chunks = [
        Chunk(
            text="ISO13485 设计开发应进行风险管理。",
            page=5,
            metadata={"filename": "ISO13485.pdf", "level": "条款"},
        ),
        Chunk(
            text="设计开发输入应包含法规要求。",
            page=5,
            metadata={"filename": "ISO13485.pdf", "level": "条款"},
        ),
        Chunk(
            text="设计开发输出应形成文件。",
            page=6,
            metadata={"filename": "ISO13485.pdf", "level": "条款"},
        ),
    ]

    ids = await client.upsert_chunks(chunks, collection=coll_name)
    assert len(ids) == 3

    results = await client.similarity_search("设计开发", top_k=2, collection=coll_name)
    assert len(results) == 2
    assert "设计开发" in results[0].text
    assert results[0].source == "[来源：ISO13485.pdf, 第5页]"


@pytest.mark.asyncio
async def test_delete_by_filename(vdb):
    client, coll_name = vdb
    """按文件名删除 → 断言检索为空。"""
    chunks = [
        Chunk(text="测试删除", page=1, metadata={"filename": "test.docx"}),
    ]
    await client.upsert_chunks(chunks, collection=coll_name)

    deleted = await client.delete_by_filename("test.docx", collection=coll_name)
    assert deleted == 1

    results = await client.similarity_search("测试", top_k=1, collection=coll_name)
    assert len(results) == 0


@pytest.mark.asyncio
async def test_ping(vdb):
    client, _ = vdb
    """健康检查。"""
    ok = await client.ping()
    assert ok is True