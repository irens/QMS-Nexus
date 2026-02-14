"""
OpenAI-API 兼容封装，支持 base_url / api_key 热切换，异步流式。
"""
import os
from typing import List, Dict, Any, Optional, AsyncIterator
import httpx
from core.models import GlobalConfig

class LLMClient:
    """线程安全、异步的 LLM 客户端，兼容任意 OpenAI-API 端点。"""

    def __init__(
        self,
        base_url: str = None,
        api_key: str = None,
        model: str = "gpt-3.5-turbo",
        timeout: int = 60,
    ):
        self.base_url = (base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")).rstrip("/")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout,
            )
        return self._client

    async def chat(
        self,
        system: str,
        user: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        stream: bool = False,
    ) -> str:
        """非流式聊天，返回完整字符串。"""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        resp = await self.client.post("/chat/completions", json=payload)
        resp.raise_for_status()
        data = await resp.json()
        return data["choices"][0]["message"]["content"]

    async def chat_stream(
        self,
        system: str,
        user: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        """流式聊天，逐句 yield。"""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        async with self.client.stream("POST", "/chat/completions", json=payload) as resp:
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    chunk = line[6:]
                    if chunk == "[DONE]":
                        break
                    data = await resp.json() if chunk else None
                    if data and data["choices"][0]["delta"].get("content"):
                        yield data["choices"][0]["delta"]["content"]

    async def ping(self) -> bool:
        """健康检查：调用 models 端点。"""
        try:
            resp = await self.client.get("/models")
            return resp.status_code == 200
        except Exception:
            return False

    async def close(self):
        """优雅关闭连接池。"""
        if self._client:
            await self._client.aclose()