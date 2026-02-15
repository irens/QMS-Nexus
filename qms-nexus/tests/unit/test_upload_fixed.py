"""
单元测试：Task 2.2 /upload 接口 (修复版)
"""
import io
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_upload_pdf():
    """上传 10 MB 以内 PDF，返回任务 ID。"""
    content = b"%PDF-1.4" + b"x" * (1024 * 1024)  # 约 1 MB
    files = {"file": ("test.pdf", io.BytesIO(content), "application/pdf")}
    resp = client.post("/api/v1/upload", files=files)  # 修复：使用正确的API前缀
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "Pending"
    assert "task_id" in data


def test_upload_unsupported_type():
    """不支持的类型返回 400。"""
    files = {"file": ("test.txt", io.BytesIO(b"hello"), "text/plain")}
    resp = client.post("/api/v1/upload", files=files)  # 修复：使用正确的API前缀
    assert resp.status_code == 400
    assert "不支持的文件类型" in resp.text