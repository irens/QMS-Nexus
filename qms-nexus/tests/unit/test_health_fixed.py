"""
单元测试：Task 2.1 /health 接口 (修复版)
"""
import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_ok(client: TestClient):
    """GET /api/v1/health → 200 {"status":"ok"}"""
    resp = client.get("/api/v1/health")  # 修复：使用正确的API前缀
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}