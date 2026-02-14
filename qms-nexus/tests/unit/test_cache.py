"""
缓存单元测试
"""
import time
import pytest
redis = pytest.importorskip("redis")  # 无 Redis 时跳过整文件
from core.cache import CacheClient


@pytest.fixture
def cache():
    return CacheClient(url="redis://localhost:6379/1")


def test_set_get(cache: CacheClient):
    cache.set("k", "v")
    assert cache.get("k") == "v"


def test_ttl_expire(cache: CacheClient):
    cache.set("k", "v", ttl=1)
    assert cache.get("k") == "v"
    time.sleep(1.1)
    assert cache.get("k") is None


def test_delete(cache: CacheClient):
    cache.set("k", "v")
    cache.delete("k")
    assert cache.get("k") is None