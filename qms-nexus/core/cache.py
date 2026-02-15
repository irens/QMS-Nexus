"""
Redis 缓存封装（TTL、序列化）
"""
import json
import redis
from typing import Any, Optional
import sys


class CacheClient:
    """问答结果缓存，默认 TTL 5 min"""

    def __init__(self, url: str = "redis://localhost:6379/1", ttl: int = 300):
        self.url = url
        self.ttl = ttl
        self.r = None
        self._connected = False
        self._connect()

    def _connect(self) -> bool:
        """尝试连接 Redis，返回是否成功"""
        try:
            self.r = redis.from_url(self.url, decode_responses=True, socket_connect_timeout=2)
            self.r.ping()
            self._connected = True
            return True
        except redis.ConnectionError:
            self._connected = False
            self.r = None
            return False
        except Exception:
            self._connected = False
            self.r = None
            return False

    def _check_connection(self) -> bool:
        """检查连接状态，如果断开则尝试重连"""
        if not self._connected or self.r is None:
            return self._connect()
        try:
            self.r.ping()
            return True
        except:
            self._connected = False
            return self._connect()

    def get(self, key: str) -> Optional[Any]:
        if not self._check_connection():
            return None
        try:
            v = self.r.get(key)
            return json.loads(v) if v else None
        except:
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if not self._check_connection():
            return
        try:
            self.r.setex(key, ttl or self.ttl, json.dumps(value, ensure_ascii=False))
        except:
            pass

    def delete(self, key: str) -> None:
        if not self._check_connection():
            return
        try:
            self.r.delete(key)
        except:
            pass

    @property
    def is_connected(self) -> bool:
        return self._check_connection()


def check_redis_connection(url: str = "redis://localhost:6379/1") -> tuple[bool, str]:
    """检查 Redis 连接状态，返回 (是否成功, 提示信息)"""
    try:
        r = redis.from_url(url, decode_responses=True, socket_connect_timeout=3)
        r.ping()
        return True, "✅ Redis 连接正常"
    except redis.ConnectionError:
        return False, """❌ Redis 连接失败

【可能原因】
1. Redis 服务未启动
2. Redis 端口被占用或配置错误

【解决方案】
1. 使用 Docker 启动 Redis：
   docker run -d --name redis -p 6379:6379 redis:latest

2. 或下载安装 Redis for Windows：
   https://github.com/microsoftarchive/redis/releases

3. 启动后请重启后端服务

【注意】
没有 Redis，系统以下功能将不可用：
- 搜索功能
- 文件上传处理
- 系统状态监控
"""
    except Exception as e:
        return False, f"❌ Redis 连接异常: {str(e)}"