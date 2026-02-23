"""
共享任务状态存储（Redis 实现）
用于在 API 和 Worker 之间共享任务状态
"""
from typing import Dict, Optional, Any
import json
import redis
from core.config import settings


class TaskStore:
    """Redis 任务状态存储，支持自动重连"""

    def __init__(self, redis_url: str = None, key_prefix: str = "qms:task:", ttl: int = 3600):
        """
        Args:
            redis_url: Redis 连接 URL，默认从配置读取
            key_prefix: Redis key 前缀
            ttl: 任务状态过期时间（秒），默认 1 小时
        """
        self.redis_url = redis_url or settings.REDIS_URL
        self.key_prefix = key_prefix
        self.ttl = ttl
        self._r = None
        self._connected = False
        self._connect()

    def _connect(self) -> bool:
        """尝试连接 Redis"""
        try:
            self._r = redis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=3,
                socket_timeout=3
            )
            self._r.ping()
            self._connected = True
            return True
        except Exception:
            self._connected = False
            self._r = None
            return False

    def _check_connection(self) -> bool:
        """检查连接状态，如果断开则尝试重连"""
        if not self._connected or self._r is None:
            return self._connect()
        try:
            self._r.ping()
            return True
        except:
            self._connected = False
            return self._connect()

    def _make_key(self, task_id: str) -> str:
        """生成 Redis key"""
        return f"{self.key_prefix}{task_id}"

    def get_task(self, task_id: str) -> Optional[dict]:
        """获取任务状态"""
        if not self._check_connection():
            return None
        try:
            key = self._make_key(task_id)
            data = self._r.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception:
            return None

    def set_task(self, task_id: str, data: dict) -> bool:
        """设置任务状态"""
        if not self._check_connection():
            return False
        try:
            key = self._make_key(task_id)
            self._r.setex(key, self.ttl, json.dumps(data, ensure_ascii=False))
            return True
        except Exception:
            return False

    def update_task_status(self, task_id: str, status: str, **kwargs) -> bool:
        """更新任务状态"""
        if not self._check_connection():
            return False
        try:
            key = self._make_key(task_id)
            data = self.get_task(task_id)
            if data is None:
                data = {}
            data["status"] = status
            for k, v in kwargs.items():
                data[k] = v
            self._r.setex(key, self.ttl, json.dumps(data, ensure_ascii=False))
            return True
        except Exception:
            return False

    def delete_task(self, task_id: str) -> bool:
        """删除任务状态"""
        if not self._check_connection():
            return False
        try:
            key = self._make_key(task_id)
            self._r.delete(key)
            return True
        except Exception:
            return False

    def get_all_tasks(self) -> Dict[str, dict]:
        """获取所有任务（用于调试）"""
        if not self._check_connection():
            return {}
        try:
            tasks = {}
            for key in self._r.scan_iter(match=f"{self.key_prefix}*"):
                task_id = key.replace(self.key_prefix, "")
                data = self._r.get(key)
                if data:
                    tasks[task_id] = json.loads(data)
            return tasks
        except Exception:
            return {}

    @property
    def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._check_connection()


# 全局 TaskStore 实例
_task_store = TaskStore()


# 兼容旧 API 的函数接口
def get_task(task_id: str) -> Optional[dict]:
    """获取任务状态"""
    return _task_store.get_task(task_id)


def set_task(task_id: str, data: dict) -> bool:
    """设置任务状态"""
    return _task_store.set_task(task_id, data)


def update_task_status(task_id: str, status: str, **kwargs) -> bool:
    """更新任务状态"""
    return _task_store.update_task_status(task_id, status, **kwargs)


def delete_task(task_id: str) -> bool:
    """删除任务状态"""
    return _task_store.delete_task(task_id)
