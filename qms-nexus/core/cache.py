"""
Redis 缓存封装（TTL、序列化）
"""
import json
import redis
from typing import Any, Optional


class CacheClient:
    """问答结果缓存，默认 TTL 5 min"""

    def __init__(self, url: str = "redis://localhost:6379/1", ttl: int = 300):
        self.r = redis.from_url(url, decode_responses=True)
        self.ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        v = self.r.get(key)
        return json.loads(v) if v else None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        self.r.setex(key, ttl or self.ttl, json.dumps(value, ensure_ascii=False))

    def delete(self, key: str) -> None:
        self.r.delete(key)