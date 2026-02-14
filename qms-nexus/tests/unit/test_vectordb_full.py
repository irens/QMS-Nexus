"""
补齐 vectordb.py 缺失分支（ping 异常）
运行：pytest tests/unit/test_vectordb_full.py -q
"""
import pytest
from unittest.mock import patch, MagicMock
from core.vectordb import VectorDBClient

@pytest.mark.asyncio
async def test_ping_false():
    """覆盖 ping 异常分支"""
    vdb = VectorDBClient()
    with patch.object(vdb, "_get_client", side_effect=Exception("conn")):
        assert await vdb.ping() is False