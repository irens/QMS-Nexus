"""
单元测试：Task 2.3 文档解析编排 Service
"""
import pytest
from pathlib import Path
from services.document_service import DocumentService


@pytest.mark.asyncio
async def test_process_pdf():
    """上传 PDF → 解析 → 入库 → 状态 Completed。"""
    svc = DocumentService()
    task_id = "test-pdf-123"
    # 使用项目内已有 PDF 或创建空文件
    pdf_path = Path("./tmp_uploads/test.pdf")
    pdf_path.parent.mkdir(exist_ok=True)
    pdf_path.write_bytes(b"%PDF-1.4")

    await svc.process(task_id, pdf_path, "application/pdf")

    status = svc.get_status(task_id)
    assert status["status"] == "Completed"


@pytest.mark.asyncio
async def test_process_excel():
    """上传 Excel → 解析 → 入库 → 状态 Completed。"""
    svc = DocumentService()
    task_id = "test-xlsx-456"
    xlsx_path = Path("./tmp_uploads/test.xlsx")
    xlsx_path.parent.mkdir(exist_ok=True)
    xlsx_path.write_bytes(b"PK")  # 伪 Excel

    await svc.process(task_id, xlsx_path, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    status = svc.get_status(task_id)
    assert status["status"] == "Completed"