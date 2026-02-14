"""
集成测试：上传→解析→检索 完整链路
"""
import io
import time
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_tmp_dir():
    Path("tmp_uploads").mkdir(exist_ok=True)


def test_pdf_upload_then_search():
    """上传 PDF → 解析 → 检索 → 断言来源"""
    # 1. 构造伪 PDF
    pdf_content = b"%PDF-1.4\n" + "质量风险管理流程示例".encode("utf-8") * 100
    files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}

    # 2. 上传
    resp = client.post("/upload", files=files)
    assert resp.status_code == 200
    task_id = resp.json()["task_id"]

    # 3. 等待后台解析（简单 sleep，CI 可换轮询）
    time.sleep(2)

    # 4. 检索
    q = "客户投诉"
    resp = client.get(f"/search?q={q}")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) > 0
    assert "客户投诉" in results[0]["text"]
    assert "test.pdf" in results[0]["source"]


def test_excel_upload_then_search():
    """上传 Excel → 解析 → 检索 → 断言来源"""
    # 1. 构造伪 Excel（PK 头）
    xlsx_content = b"PK" + "检验规范表格".encode("utf-8") * 100
    files = {"file": ("test.xlsx", io.BytesIO(xlsx_content),
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}

    # 2. 上传
    resp = client.post("/upload", files=files)
    assert resp.status_code == 200
    task_id = resp.json()["task_id"]

    # 3. 等待后台解析
    time.sleep(2)

    # 4. 检索
    q = "检验规范"
    resp = client.get(f"/search?q={q}")
    assert resp.status_code == 200
    results = resp.json()
    assert len(results) > 0
    assert "检验规范" in results[0]["text"]
    assert "test.xlsx" in results[0]["source"]


def test_upload_poll_until_completed():
    """上传 → 轮询状态直到 Completed"""
    pdf_content = b"%PDF-1.4\n" + "设计开发".encode("utf-8") * 100
    files = {"file": ("poll.pdf", io.BytesIO(pdf_content), "application/pdf")}
    resp = client.post("/upload", files=files)
    assert resp.status_code == 200
    task_id = resp.json()["task_id"]

    # 轮询状态，最多 30 秒
    for _ in range(60):
        r = client.get(f"/upload/status/{task_id}")
        assert r.status_code == 200
        status = r.json()["status"]
        if status == "Completed":
            break
        if status == "Failed":
            pytest.fail("任务失败")
        time.sleep(0.5)
    else:
        pytest.fail("超时未 Completed")