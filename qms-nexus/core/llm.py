"""
OpenAI-API 兼容封装，支持 base_url / api_key 热切换，异步流式。
支持多模型降级、自动重试、Token使用量记录。
"""
import os
import json
import asyncio
from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass
import httpx

from core.config import settings
from core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ChatResult:
    """聊天结果"""
    text: str
    model_used: str
    tokens_used: int
    is_fallback: bool = False


class LLMError(Exception):
    """LLM调用错误"""
    pass


class LLMClient:
    """线程安全、异步的 LLM 客户端，兼容任意 OpenAI-API 端点。
    
    特性：
    - 支持多模型自动降级
    - 自动重试机制（指数退避）
    - Token使用量记录
    - 流式/非流式输出
    """

    def __init__(
        self,
        base_url: str = None,
        api_key: str = None,
        model: str = None,
        timeout: int = None,
    ):
        self.base_url = (base_url or settings.LLM_BASE_URL or "https://api.openai.com/v1").rstrip("/")
        self.api_key = api_key or settings.LLM_API_KEY or os.getenv("OPENAI_API_KEY")
        self.model = model or settings.LLM_MODEL or "gpt-3.5-turbo"
        self.timeout = timeout or settings.LLM_TIMEOUT or 60
        
        # 解析备选模型列表
        try:
            self.fallback_models = json.loads(settings.LLM_FALLBACK_MODELS or '["gpt-3.5-turbo"]')
        except json.JSONDecodeError:
            self.fallback_models = ["gpt-3.5-turbo"]
        
        self._client: Optional[httpx.AsyncClient] = None
        
        logger.info(f"LLMClient初始化: model={self.model}, fallback_models={self.fallback_models}")

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self.timeout,
            )
        return self._client

    async def _chat_single(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 1024,
        stream: bool = False,
    ) -> ChatResult:
        """单次调用LLM，带重试机制。
        
        Args:
            model: 模型名称
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出
            
        Returns:
            ChatResult: 聊天结果
            
        Raises:
            LLMError: 调用失败
        """
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream,
        }
        
        # 最多重试3次，指数退避：1s, 2s, 4s
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.debug(f"调用LLM: model={model}, attempt={attempt + 1}")
                
                resp = await self.client.post("/chat/completions", json=payload)
                
                # 特定错误不重试（如401认证失败）
                if resp.status_code == 401:
                    raise LLMError(f"认证失败: {resp.text}")
                if resp.status_code == 403:
                    raise LLMError(f"权限不足: {resp.text}")
                if resp.status_code == 400:
                    raise LLMError(f"请求参数错误: {resp.text}")
                
                resp.raise_for_status()
                data = resp.json()
                
                # 提取结果
                text = data["choices"][0]["message"]["content"]
                tokens_used = data.get("usage", {}).get("total_tokens", 0)
                
                logger.debug(f"LLM调用成功: model={model}, tokens={tokens_used}")
                
                return ChatResult(
                    text=text,
                    model_used=model,
                    tokens_used=tokens_used,
                )
                
            except httpx.TimeoutException as e:
                last_error = f"超时: {e}"
                logger.warning(f"LLM调用超时 (attempt {attempt + 1}/{max_retries}): {e}")
                
            except httpx.HTTPStatusError as e:
                last_error = f"HTTP错误 {e.response.status_code}: {e.response.text}"
                logger.warning(f"LLM调用HTTP错误 (attempt {attempt + 1}/{max_retries}): {last_error}")
                
                # 5xx错误可以重试
                if e.response.status_code < 500:
                    raise LLMError(last_error)
                    
            except Exception as e:
                last_error = f"未知错误: {e}"
                logger.warning(f"LLM调用失败 (attempt {attempt + 1}/{max_retries}): {e}")
            
            # 指数退避等待
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # 1s, 2s, 4s
                logger.debug(f"等待 {wait_time}s 后重试...")
                await asyncio.sleep(wait_time)
        
        # 所有重试都失败
        raise LLMError(f"LLM调用失败（已重试{max_retries}次）: {last_error}")

    async def chat(
        self,
        system: str,
        user: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        stream: bool = False,
    ) -> ChatResult:
        """聊天调用，支持自动降级。
        
        流程：
        1. 尝试主模型
        2. 主模型失败时依次尝试备选模型
        3. 记录使用的模型和token数
        
        Args:
            system: 系统提示词
            user: 用户输入
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出（当前非流式）
            
        Returns:
            ChatResult: 聊天结果
        """
        messages = [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ]
        
        # 尝试主模型
        models_to_try = [self.model] + self.fallback_models
        last_error = None
        
        for idx, model in enumerate(models_to_try):
            try:
                is_fallback = idx > 0
                
                result = await self._chat_single(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=stream,
                )
                
                # 标记是否使用了降级模型
                result.is_fallback = is_fallback
                
                if is_fallback:
                    logger.info(f"使用降级模型成功: {model}")
                
                return result
                
            except LLMError as e:
                last_error = str(e)
                logger.warning(f"模型 {model} 调用失败: {e}")
                continue
            except Exception as e:
                last_error = str(e)
                logger.error(f"模型 {model} 调用异常: {e}")
                continue
        
        # 所有模型都失败
        logger.error(f"所有模型调用失败: {last_error}")
        raise LLMError(f"所有模型调用失败: {last_error}")

    async def chat_stream(
        self,
        system: str,
        user: str,
        temperature: float = 0.3,
        max_tokens: int = 1024,
    ) -> AsyncIterator[str]:
        """流式聊天，逐句 yield。
        
        Args:
            system: 系统提示词
            user: 用户输入
            temperature: 温度参数
            max_tokens: 最大token数
            
        Yields:
            str: 文本片段
        """
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
        
        try:
            async with self.client.stream("POST", "/chat/completions", json=payload) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        chunk = line[6:]
                        if chunk == "[DONE]":
                            break
                        try:
                            data = json.loads(chunk)
                            if data.get("choices") and data["choices"][0].get("delta"):
                                content = data["choices"][0]["delta"].get("content")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            logger.error(f"流式调用失败: {e}")
            raise LLMError(f"流式调用失败: {e}")

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
            self._client = None
