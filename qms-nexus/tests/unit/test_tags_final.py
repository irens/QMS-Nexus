"""
单元测试：Task 2.5 标签 CRUD
"""
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_create_tag():
    """新增标签。"""
    resp = client.post("/tags", json={"tag": "ISO13485", "description": "质量体系"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["tag"] == "ISO13485"
    assert data["description"] == "质量体系"


def test_list_tags():
    """列出全部标签。"""
    resp = client.get("/tags")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert any(t["tag"] == "ISO13485" for t in data)


def test_update_tag():
    """更新标签描述。"""
    resp = client.put("/tags/ISO13485", json={"description": "医疗器械质量体系"})
    assert resp.status_code == 200
    assert resp.json()["description"] == "医疗器械质量体系"


def test_get_tag():
    """获取单个标签。"""
    resp = client.get("/tags/ISO13485")
    assert resp.status_code == 200
    assert resp.json()["tag"] == "ISO13485"


def test_delete_tag():
    """删除标签。"""
    resp = client.delete("/tags/ISO13485")
    assert resp.status_code == 200
    # 再次获取应 404
    resp = client.get("/tags/ISO13485")
    assert resp.status_code == 404