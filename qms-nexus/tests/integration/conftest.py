"""
QMS-Nexus 集成测试 Fixtures
提供测试专用的临时数据库和 ChromaDB 集合
"""
import asyncio
import json
import tempfile
import uuid
from pathlib import Path
from typing import AsyncGenerator, Dict, Any

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

from api.main import app
from core.rag_service import RAGService
from core.vectordb import VectorDBClient


@pytest.fixture(scope="session")
def test_data_dir() -> Path:
    """测试数据目录"""
    return Path(__file__).parent / "data"


@pytest.fixture(scope="session")
def sample_pdf_path(test_data_dir: Path) -> Path:
    """测试用的PDF文件路径"""
    pdf_path = test_data_dir / "test_document.pdf"
    test_data_dir.mkdir(exist_ok=True)
    
    # 创建一个简单的测试PDF文件（ASCII内容）
    pdf_content = (
        b"%%PDF-1.4\n"
        b"1 0 obj\n"
        b"<<\n"
        b"/Type /Catalog\n"
        b"/Pages 2 0 R\n"
        b">>\n"
        b"endobj\n"
        b"2 0 obj\n"
        b"<<\n"
        b"/Type /Pages\n"
        b"/Kids [3 0 R]\n"
        b"/Count 1\n"
        b">>\n"
        b"endobj\n"
        b"3 0 obj\n"
        b"<<\n"
        b"/Type /Page\n"
        b"/Parent 2 0 R\n"
        b"/MediaBox [0 0 612 792]\n"
        b"/Contents 4 0 R\n"
        b">>\n"
        b"endobj\n"
        b"4 0 obj\n"
        b"<<\n"
        b"/Length 50\n"
        b">>\n"
        b"stream\n"
        b"BT\n"
        b"/F1 12 Tf\n"
        b"100 700 Td\n"
        b"(Test Document Content) Tj\n"
        b"ET\n"
        b"endstream\n"
        b"endobj\n"
        b"xref\n"
        b"0 5\n"
        b"0000000000 65535 f \n"
        b"0000000010 00000 n \n"
        b"0000000053 00000 n \n"
        b"0000000100 00000 n \n"
        b"0000000180 00000 n \n"
        b"trailer\n"
        b"<<\n"
        b"/Size 5\n"
        b"/Root 1 0 R\n"
        b">>\n"
        b"startxref\n"
        b"280\n"
        b"%%EOF"
    )
    
    pdf_path.write_bytes(pdf_content)
    return pdf_path


@pytest.fixture(scope="session")
def test_vector_collection_name() -> str:
    """测试用的ChromaDB集合名称"""
    return f"test_collection_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="session")
def test_vector_store(test_vector_collection_name: str) -> VectorDBClient:
    """测试向量存储"""
    # 使用临时目录进行测试
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        store = VectorDBClient(
            persist_dir=tmpdir,
            collection_name=test_vector_collection_name
        )
        yield store


@pytest.fixture(scope="session")
def test_rag_service(test_vector_store: VectorDBClient) -> RAGService:
    """测试RAG服务"""
    return RAGService(vector_store=test_vector_store)


@pytest.fixture(scope="session")
def test_client() -> TestClient:
    """FastAPI测试客户端"""
    with TestClient(app) as client:
        yield client


@pytest.fixture(scope="session")
def mock_llm_response() -> Dict[str, Any]:
    """Mock LLM响应数据"""
    return {
        "choices": [{
            "message": {
                "content": "根据文档内容，这是一个关于质量管理体系的测试文档。主要内容包括质量方针、目标和管理职责。",
                "role": "assistant"
            }
        }],
        "usage": {
            "total_tokens": 150,
            "prompt_tokens": 50,
            "completion_tokens": 100
        }
    }


@pytest.fixture(scope="session")
def mock_embeddings() -> list:
    """Mock向量嵌入"""
    # 返回512维的测试向量（与EmbeddingConfig.dim匹配）
    return [0.1] * 512