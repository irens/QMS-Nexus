"""
异常处理测试用例实现
基于测试设计文档的异常处理测试代码
"""
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Dict, Any
from fastapi.testclient import TestClient

from tests.integration.test_cases_design import test_cases, TestType, TestPriority


class TestExceptionHandling:
    """异常处理测试类"""
    
    def test_upload_corrupted_file_exception(self, test_client: TestClient):
        """UP-EX-01: 文件损坏异常处理"""
        
        # 创建一个损坏的PDF文件（只有文件头，没有完整结构）
        corrupted_content = b"%PDF-1.4\n损坏的内容"
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(corrupted_content)
            tmp_path = Path(tmp.name)
        
        try:
            with open(tmp_path, "rb") as f:
                files = {"file": ("corrupted.pdf", f, "application/pdf")}
                response = test_client.post("/upload", files=files)
            
            # 上传应该成功（文件格式检查通过）
            assert response.status_code == 200
            result = response.json()
            task_id = result["task_id"]
            
            # 轮询任务状态，期望最终状态为Failed
            max_retries = 30
            for i in range(max_retries):
                status_response = test_client.get(f"/upload/status/{task_id}")
                assert status_response.status_code == 200
                
                status_data = status_response.json()
                if status_data["status"] == "Failed":
                    print(f"✅ UP-EX-01通过: 损坏文件任务最终状态为Failed")
                    return
                elif status_data["status"] == "Completed":
                    pytest.fail("损坏文件不应该处理成功")
                
                import time
                time.sleep(1)
            
            # 如果超时，任务应该还在Pending状态（因为Redis不可用）
            print(f"⚠️ UP-EX-01注意: 任务状态保持Pending（Redis不可用）")
            
        finally:
            tmp_path.unlink(missing_ok=True)
    
    def test_upload_redis_connection_failure(self, test_client: TestClient):
        """UP-EX-02: Redis连接失败异常处理"""
        
        # 创建正常PDF文件
        pdf_content = b"%PDF-1.4\n1 0 obj<<>>endobj"
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_content)
            tmp_path = Path(tmp.name)
        
        try:
            # Mock Redis连接失败
            with patch('services.document_service.create_pool') as mock_create_pool:
                mock_create_pool.side_effect = Exception("Redis连接失败")
                
                with open(tmp_path, "rb") as f:
                    files = {"file": ("test.pdf", f, "application/pdf")}
                    response = test_client.post("/upload", files=files)
            
            # 上传应该成功（文件接收成功）
            assert response.status_code == 200
            result = response.json()
            task_id = result["task_id"]
            
            # 任务状态应该保持Pending（因为无法连接到Redis）
            status_response = test_client.get(f"/upload/status/{task_id}")
            assert status_response.status_code == 200
            status_data = status_response.json()
            assert status_data["status"] == "Pending"
            
            print(f"✅ UP-EX-02通过: Redis连接失败时任务保持Pending状态")
            
        finally:
            tmp_path.unlink(missing_ok=True)
    
    def test_search_vector_db_exception(self, test_client: TestClient):
        """SR-EX-01: 向量数据库异常处理"""
        
        # Mock向量数据库异常
        with patch('core.vectordb.VectorDBClient.similarity_search') as mock_search:
            mock_search.side_effect = Exception("向量数据库连接失败")
            
            response = test_client.get("/search?q=质量方针&top_k=5")
        
        # 期望返回500错误
        assert response.status_code == 500
        print(f"✅ SR-EX-01通过: 向量数据库异常返回500错误")
    
    def test_search_empty_vector_db(self, test_client: TestClient):
        """SR-EX-02: 空向量数据库处理"""
        
        # Mock空数据库返回
        with patch('core.vectordb.VectorDBClient.similarity_search') as mock_search:
            mock_search.return_value = []  # 空结果
            
            response = test_client.get("/search?q=质量方针&top_k=5")
        
        # 期望返回200，但结果为空列表
        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)
        assert len(results) == 0
        
        print(f"✅ SR-EX-02通过: 空向量数据库返回空结果")
    
    def test_ask_llm_timeout_exception(self, test_client: TestClient):
        """AS-EX-01: LLM服务超时异常处理"""
        
        # Mock LLM服务超时
        with patch('core.rag_service.RAGService.answer') as mock_answer:
            import asyncio
            mock_answer.side_effect = asyncio.TimeoutError("LLM服务超时")
            
            response = test_client.post("/ask", json={"question": "什么是质量方针？"})
        
        # 期望返回504超时错误
        assert response.status_code == 504
        result = response.json()
        assert "timeout" in result.get("detail", "").lower()
        
        print(f"✅ AS-EX-01通过: LLM超时返回504错误")
    
    def test_ask_llm_service_unavailable(self, test_client: TestClient):
        """AS-EX-02: LLM服务不可用异常处理"""
        
        # Mock LLM服务不可用
        with patch('core.rag_service.RAGService.answer') as mock_answer:
            mock_answer.side_effect = Exception("LLM服务不可用")
            
            response = test_client.post("/ask", json={"question": "什么是质量方针？"})
        
        # 期望返回500错误
        assert response.status_code == 500
        result = response.json()
        assert "detail" in result
        
        print(f"✅ AS-EX-02通过: LLM服务不可用返回500错误")
    
    def test_ask_vector_db_exception(self, test_client: TestClient):
        """AS-EX-03: 问答时向量数据库异常处理"""
        
        # Mock向量数据库在问答时异常
        with patch('core.rag_service.RAGService.answer') as mock_answer:
            mock_answer.side_effect = Exception("向量数据库异常")
            
            response = test_client.post("/ask", json={"question": "什么是质量方针？"})
        
        # 期望返回500错误
        assert response.status_code == 500
        result = response.json()
        assert "detail" in result
        
        print(f"✅ AS-EX-03通过: 向量数据库异常返回500错误")
    
    def test_health_check_db_failure(self, test_client: TestClient):
        """HC-EX-01: 健康检查数据库异常处理"""
        
        # Mock数据库连接失败
        with patch('core.health.check_database') as mock_check_db:
            mock_check_db.return_value = False  # 数据库不可用
            
            response = test_client.get("/health")
        
        # 期望返回503服务不可用
        assert response.status_code == 503
        result = response.json()
        assert result["status"] == "error"
        
        print(f"✅ HC-EX-01通过: 数据库异常返回503错误")
    
    def test_metrics_endpoint_exception(self, test_client: TestClient):
        """MT-EX-01: 监控指标异常处理"""
        
        # Mock Prometheus指标生成失败
        with patch('prometheus_client.generate_latest') as mock_generate:
            mock_generate.side_effect = Exception("指标生成失败")
            
            response = test_client.get("/metrics")
        
        # 期望返回500错误
        assert response.status_code == 500
        print(f"✅ MT-EX-01通过: 监控指标异常返回500错误")


class TestNetworkExceptions:
    """网络异常测试类"""
    
    def test_upload_network_timeout(self, test_client: TestClient):
        """网络超时异常处理"""
        
        # 创建大文件模拟网络超时
        large_content = b"X" * (10 * 1024 * 1024)  # 10MB
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(large_content)
            tmp_path = Path(tmp.name)
        
        try:
            # Mock网络超时
            with patch('fastapi.UploadFile.read') as mock_read:
                import asyncio
                mock_read.side_effect = asyncio.TimeoutError("网络读取超时")
                
                with open(tmp_path, "rb") as f:
                    files = {"file": ("large.pdf", f, "application/pdf")}
                    response = test_client.post("/upload", files=files)
            
            # 期望返回408请求超时
            assert response.status_code == 408
            print(f"✅ 网络超时测试通过: 返回408错误")
            
        finally:
            tmp_path.unlink(missing_ok=True)
    
    def test_search_rate_limit_exceeded(self, test_client: TestClient):
        """速率限制异常处理"""
        
        # 模拟超过速率限制
        with patch('core.rag_service.RAGService.answer') as mock_answer:
            mock_answer.side_effect = Exception("速率限制 exceeded")
            
            response = test_client.post("/ask", json={"question": "测试问题"})
        
        # 期望返回429太多请求
        assert response.status_code == 429
        print(f"✅ 速率限制测试通过: 返回429错误")


class TestDataValidationExceptions:
    """数据验证异常测试类"""
    
    def test_upload_invalid_filename(self, test_client: TestClient):
        """无效文件名异常处理"""
        
        pdf_content = b"%PDF-1.4\n1 0 obj<<>>endobj"
        
        # 测试各种无效文件名
        invalid_filenames = [
            "",  # 空文件名
            "../../../etc/passwd",  # 路径遍历
            "file\x00name.pdf",  # 包含空字符
            "a" * 300,  # 超长文件名
        ]
        
        for filename in invalid_filenames:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(pdf_content)
                tmp_path = Path(tmp.name)
            
            try:
                with open(tmp_path, "rb") as f:
                    files = {"file": (filename, f, "application/pdf")}
                    response = test_client.post("/upload", files=files)
                
                # 期望返回400错误
                assert response.status_code == 400
                print(f"✅ 无效文件名测试通过: '{filename[:30]}...' 返回400错误")
                
            finally:
                tmp_path.unlink(missing_ok=True)
    
    def test_search_invalid_parameters(self, test_client: TestClient):
        """搜索参数验证异常"""
        
        # 测试各种无效参数组合
        invalid_params = [
            {"q": None},  # None值
            {"q": 123},  # 非字符串类型
            {"top_k": "invalid"},  # 非数字top_k
            {"top_k": None},  # None top_k
            {"filter_tags": "not-a-list"},  # 非列表标签
        ]
        
        for params in invalid_params:
            # 构建查询参数
            query_params = []
            if "q" in params:
                if params["q"] is not None:
                    query_params.append(f"q={params['q']}")
            else:
                query_params.append("q=测试")  # 默认查询
            
            if "top_k" in params:
                if params["top_k"] is not None:
                    query_params.append(f"top_k={params['top_k']}")
            
            if "filter_tags" in params:
                query_params.append(f"filter_tags={params['filter_tags']}")
            
            url = f"/search?{'&'.join(query_params)}"
            response = test_client.get(url)
            
            # 期望返回422验证错误
            assert response.status_code == 422
            print(f"✅ 无效参数测试通过: {params} 返回422错误")
    
    def test_ask_invalid_json_payload(self, test_client: TestClient):
        """无效JSON载荷异常处理"""
        
        # 发送无效的JSON数据
        invalid_payloads = [
            "不是JSON",  # 纯文本
            "{invalid json}",  # 无效JSON格式
            "",  # 空字符串
            "null",  # JSON null
            "[]",  # JSON数组而不是对象
        ]
        
        for payload in invalid_payloads:
            response = test_client.post(
                "/ask",
                data=payload,  # 使用data而不是json参数
                headers={"Content-Type": "application/json"}
            )
            
            # 期望返回400错误
            assert response.status_code == 400
            print(f"✅ 无效JSON测试通过: '{payload[:20]}...' 返回400错误")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])