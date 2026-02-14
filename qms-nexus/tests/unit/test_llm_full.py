"""
补齐 llm.py 缺失分支的单元测试（stream / ping / close）
运行：pytest tests/unit/test_llm.py -q
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from core.llm import LLMClient

@pytest.mark.asyncio
async def test_stream_full_coverage():
    """覆盖 stream 分支 & yield 内容"""
    llm = LLMClient(api_key="sk-fake")
    # mock 返回逐句 SSE
    mock_resp = MagicMock()
    mock_resp.aiter_lines = AsyncMock()
    mock_resp.aiter_lines.return_value = [
        'data: {"choices":[{"delta":{"content":"hello"}}]}',
        'data: {"choices":[{"delta":{"content":" world"}}]}',
        'data: [DONE]'
    ]
    with patch.object(llm.client, "stream", return_value=mock_resp):
        chunks = []
        async for c in llm.chat_stream(system="sys", user="hi"):
            chunks.append(c)
        assert chunks == ["hello", " world"]

@pytest.mark.asyncio
async def test_ping_success():
    """覆盖 ping 成功分支"""
    llm = LLMClient(api_key="sk-fake")
    with patch.object(llm.client, "get", return_value=MagicMock(status_code=200)):
        assert await llm.ping() is True

@pytest.mark.asyncio
async def test_ping_failure():
    """覆盖 ping 异常分支"""
    llm = LLMClient(api_key="sk-fake")
    with patch.object(llm.client, "get", side_effect=Exception("timeout")):
        assert await llm.ping() is False

@pytest.mark.asyncio
async def test_close():
    """覆盖 close 分支"""
    llm = LLMClient(api_key="sk-fake")
    llm._client = MagicMock()
    llm._client.aclose = AsyncMock()
    await llm.close()
    llm._client.aclose.assert_awaited_once()