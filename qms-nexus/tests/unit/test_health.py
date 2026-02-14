"""
单元测试：Task 2.1 /health 接口
"""
import pytest
from fastapi.testclient import TestClient
from api.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_ok(client: TestClient):
    """GET /health → 200 {"status":"ok"}"""
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}