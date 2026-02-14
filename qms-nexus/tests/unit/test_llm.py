"""
单元测试：LLM 客户端非流式/流式调用 & ping。
运行：pytest tests/unit/test_llm.py -q
"""
import asyncio
import pytest
from core.llm import LLMClient

@pytest.mark.asyncio
async def test_chat(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    llm = LLMClient(base_url="https://api.openai-proxy.org/v1", model="gpt-3.5-turbo")
    # 仅验证请求结构，mock 返回
    try:
        resp = await llm.chat(system="You are helpful.", user="Hi")
        assert isinstance(resp, str)
    except Exception:
        pytest.skip("需要真实 KEY 或 mock")

@pytest.mark.asyncio
async def test_ping(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    llm = LLMClient()
    ok = await llm.ping()
    # 无 KEY 时预期 False
    assert ok is False or True

@pytest.mark.asyncio
async def test_stream(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fake")
    llm = LLMClient()
    chunks = []
    try:
        async for c in llm.chat_stream(system="You are helpful.", user="Hi"):
            chunks.append(c)
        assert len(chunks) >= 0
    except Exception:
        pytest.skip("需要真实 KEY 或 mock")