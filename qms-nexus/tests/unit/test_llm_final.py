"""
单元测试：core/llm.py 流式/非流式 + 热切换
"""
import pytest
from unittest.mock import AsyncMock, patch
from core.llm import LLMClient


@pytest.mark.asyncio
async def test_chat_non_stream():
    """非流式返回完整字符串。"""
    llm = LLMClient(base_url="http://fake", api_key="fake", model="gpt-4")
    # 模拟返回
    async def mock_post(*a, **k):
        resp = AsyncMock()
        resp.status_code = 200
        resp.json = AsyncMock(return_value={"choices": [{"message": {"content": "答案是 42。"}}]})
        return resp

    with patch.object(llm.client, "post", side_effect=mock_post):
        answer = await llm.chat(system="QMS", user="ISO13485 核心？")
        assert answer == "答案是 42。"


@pytest.mark.asyncio
async def test_ping_ok():
    """健康检查通过。"""
    llm = LLMClient(base_url="http://fake", api_key="fake")
    async def mock_get(*a, **k):
        resp = AsyncMock()
        resp.status_code = 200
        return resp
    with patch.object(llm.client, "get", side_effect=mock_get):
        ok = await llm.ping()
        assert ok is True


@pytest.mark.asyncio
async def test_ping_fail():
    """健康检查失败。"""
    llm = LLMClient(base_url="http://fake", api_key="fake")
    with patch.object(llm.client, "get", side_effect=Exception("timeout")):
        ok = await llm.ping()
        assert ok is False