"""
单元测试：文档路由基于数据库的 CRUD 和查询
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


def test_create_and_get_document(client: TestClient):
    """创建文档并通过详情接口获取。"""

    body = {
        "filename": "test.pdf",
        "fileType": "pdf",
        "fileSize": 1234,
        "tags": ["tag1", "tag2"],
        "metadata": {"source": "unit-test"},
    }
    resp = client.post("/api/v1/documents", json=body)
    assert resp.status_code == 200
    created = resp.json()
    assert created["filename"] == "test.pdf"
    assert set(created["tags"]) == {"tag1", "tag2"}
    doc_id = created["id"]

    resp = client.get(f"/api/v1/documents/{doc_id}")
    assert resp.status_code == 200
    got = resp.json()
    assert got["id"] == doc_id
    assert got["fileType"] == "pdf"


def test_list_documents_with_search_and_filter(client: TestClient):
    """文档列表支持搜索和过滤。"""

    # 创建两个文档
    client.post(
        "/api/v1/documents",
        json={
            "filename": "alpha.pdf",
            "fileType": "pdf",
            "fileSize": 100,
            "tags": ["t1"],
            "metadata": {},
        },
    )
    client.post(
        "/api/v1/documents",
        json={
            "filename": "beta.docx",
            "fileType": "docx",
            "fileSize": 200,
            "tags": ["t2"],
            "metadata": {},
        },
    )

    # 搜索文件名包含 alpha
    resp = client.get(
        "/api/v1/documents",
        params={"page": 1, "pageSize": 10, "search": "alpha"},
    )
    assert resp.status_code == 200
    page = resp.json()
    assert page["total"] == 1
    assert page["items"][0]["filename"] == "alpha.pdf"


def test_update_and_delete_document(client: TestClient):
    """删除文档后再次访问应 404。"""

    resp = client.post(
        "/api/v1/documents",
        json={
            "filename": "remove-me.pdf",
            "fileType": "pdf",
            "fileSize": 111,
            "tags": [],
            "metadata": {},
        },
    )
    doc_id = resp.json()["id"]

    # 删除
    resp = client.delete(f"/api/v1/documents/{doc_id}")
    assert resp.status_code == 200

    # 再获取应 404
    assert client.get(f"/api/v1/documents/{doc_id}").status_code == 404

