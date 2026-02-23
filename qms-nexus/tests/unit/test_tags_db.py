"""
单元测试：标签路由基于数据库的 CRUD
"""
from fastapi.testclient import TestClient
import pytest

from api.main import app
from core.database import db_manager


@pytest.fixture(autouse=True)
def setup_database():
    """为每个测试用例重建数据库表，避免相互影响。"""

    db_manager.drop_all_tables()
    db_manager.create_tables()
    yield


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def test_create_and_get_tag(client: TestClient):
    """创建标签并通过列表和详情接口获取。"""

    resp = client.post(
        "/api/v1/tags",
        json={"name": "ISO13485", "description": "质量体系", "color": "#123456"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "ISO13485"
    assert data["description"] == "质量体系"
    assert data["color"] == "#123456"
    tag_id = data["id"]

    # 列表应包含该标签
    resp = client.get("/api/v1/tags", params={"page": 1, "pageSize": 10})
    assert resp.status_code == 200
    page = resp.json()
    assert page["total"] == 1
    assert any(item["id"] == tag_id for item in page["items"])

    # 详情接口
    resp = client.get(f"/api/v1/tags/{tag_id}")
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["id"] == tag_id
    assert detail["name"] == "ISO13485"


def test_create_duplicate_tag_conflict(client: TestClient):
    """同名标签创建应返回 409。"""

    body = {"name": "QMS", "description": "质量管理", "color": "#409EFF"}
    assert client.post("/api/v1/tags", json=body).status_code == 200
    resp = client.post("/api/v1/tags", json=body)
    assert resp.status_code == 409


def test_update_and_delete_tag(client: TestClient):
    """更新和删除标签。"""

    resp = client.post(
        "/api/v1/tags",
        json={"name": "OldName", "description": "desc", "color": "#000000"},
    )
    tag_id = resp.json()["id"]

    # 更新名称和描述
    resp = client.put(
        f"/api/v1/tags/{tag_id}",
        json={"name": "NewName", "description": "new desc"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "NewName"
    assert data["description"] == "new desc"

    # 删除
    resp = client.delete(f"/api/v1/tags/{tag_id}")
    assert resp.status_code == 200

    # 再次获取应 404
    assert client.get(f"/api/v1/tags/{tag_id}").status_code == 404

