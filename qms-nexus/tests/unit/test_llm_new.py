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
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    mock_resp.json = AsyncMock(return_value={
        "choices": [{"message": {"content": "答案是 42。"}}]
    })
    with patch.object(llm.client, "post", AsyncMock(return_value=mock_resp)) as mock_post:
        answer = await llm.chat(system="QMS", user="ISO13485 核心？")
        assert answer == "答案是 42。"
        mock_post.assert_awaited_once()


@pytest.mark.asyncio
async def test_chat_stream():
    """流式逐句 yield。"""
    llm = LLMClient(base_url="http://fake", api_key="fake", model="gpt-4")
    mock_resp = AsyncMock()
    mock_resp.aiter_lines = AsyncMock(
        return_value=[
            "data: {\"choices\":[{\"delta\":{\"content\":\"A\"}}]}",
            "data: {\"choices\":[{\"delta\":{\"content\":\"B\"}}]}",
            "data: [DONE]",
        ]
    )
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=None)
    with patch.object(llm.client, "stream", AsyncMock(return_value=mock_resp)) as mock_stream:
        chunks = [c async for c in llm.chat_stream(system="QMS", user="？")]
        assert chunks == ["A", "B"]
        mock_stream.assert_awaited_once()


@pytest.mark.asyncio
async def test_ping_ok():
    """健康检查通过。"""
    llm = LLMClient(base_url="http://fake", api_key="fake")
    mock_resp = AsyncMock()
    mock_resp.status_code = 200
    with patch.object(llm.client, "get", return_value=mock_resp) as mock_get:
        ok = await llm.ping()
        assert ok is True
        mock_get.assert_awaited_once()


@pytest.mark.asyncio
async def test_ping_fail():
    """健康检查失败。"""
    llm = LLMClient(base_url="http://fake", api_key="fake")
    with patch.object(llm.client, "get", side_effect=Exception("timeout")):
        ok = await llm.ping()
        assert ok is False