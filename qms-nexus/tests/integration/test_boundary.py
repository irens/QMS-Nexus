"""
边界值测试用例实现
基于测试设计文档的具体测试代码
"""
import pytest
import tempfile
import uuid
from pathlib import Path
from typing import Dict, Any
from fastapi.testclient import TestClient

from tests.integration.test_cases_design import test_cases, TestType, TestPriority
from tests.integration.utils import poll_task_status


class TestBoundaryValues:
    """边界值测试类"""
    
    def test_upload_file_size_boundary_minimum(self, test_client: TestClient):
        """UP-BV-01: 文件大小边界-最小值(0字节)"""
        # 创建0字节PDF文件
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            with open(tmp_path, "rb") as f:
                files = {"file": ("empty.pdf", f, "application/pdf")}
                response = test_client.post("/upload", files=files)
            
            # 期望返回400错误（文件内容为空）
            assert response.status_code == 400
            result = response.json()
            assert "detail" in result
            print(f"✅ UP-BV-01通过: 0字节文件返回{response.status_code}")
            
        finally:
            tmp_path.unlink(missing_ok=True)
    
    def test_upload_file_size_boundary_exactly_50mb(self, test_client: TestClient):
        """UP-BV-02: 文件大小边界-刚好50MB"""
        # 创建刚好50MB的PDF文件
        content_size = 50 * 1024 * 1024
        pdf_header = b"%PDF-1.4\n"
        padding = b"X" * (content_size - len(pdf_header))
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_header + padding)
            tmp_path = Path(tmp.name)
        
        try:
            with open(tmp_path, "rb") as f:
                files = {"file": ("large_50mb.pdf", f, "application/pdf")}
                response = test_client.post("/upload", files=files)
            
            # 期望返回200成功
            assert response.status_code == 200
            result = response.json()
            assert "task_id" in result
            assert result["status"] == "Pending"
            print(f"✅ UP-BV-02通过: 50MB文件上传成功")
            
        finally:
            tmp_path.unlink(missing_ok=True)
    
    def test_upload_file_size_boundary_over_50mb(self, test_client: TestClient):
        """UP-BV-03: 文件大小边界-超过50MB"""
        # 创建51MB的PDF文件（超过限制）
        content_size = 51 * 1024 * 1024
        pdf_header = b"%PDF-1.4\n"
        padding = b"X" * (content_size - len(pdf_header))
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_header + padding)
            tmp_path = Path(tmp.name)
        
        try:
            with open(tmp_path, "rb") as f:
                files = {"file": ("oversized_51mb.pdf", f, "application/pdf")}
                response = test_client.post("/upload", files=files)
            
            # 期望返回413错误（文件过大）
            assert response.status_code == 413
            result = response.json()
            assert "文件超过 50 MB" in result.get("detail", "")
            print(f"✅ UP-BV-03通过: 51MB文件返回413错误")
            
        finally:
            tmp_path.unlink(missing_ok=True)
    
    def test_upload_content_type_boundary_empty(self, test_client: TestClient):
        """UP-BV-04: Content-Type边界-空值"""
        # 创建测试PDF文件
        pdf_content = b"%PDF-1.4\n1 0 obj<<>>endobj"
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_content)
            tmp_path = Path(tmp.name)
        
        try:
            with open(tmp_path, "rb") as f:
                # 模拟缺少Content-Type的情况
                # FastAPI会自动检测，我们需要测试边界情况
                files = {"file": ("test.pdf", f, None)}  # None表示缺少Content-Type
                response = test_client.post("/upload", files=files)
            
            # 期望返回400错误（缺少Content-Type）
            assert response.status_code == 400
            result = response.json()
            assert "缺少 Content-Type" in result.get("detail", "")
            print(f"✅ UP-BV-04通过: 空Content-Type返回400错误")
            
        finally:
            tmp_path.unlink(missing_ok=True)
    
    def test_upload_content_type_boundary_invalid(self, test_client: TestClient):
        """UP-BV-05: Content-Type边界-格式错误"""
        # 创建测试文件
        content = b"test content"
        
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            tmp.write(content)
            tmp_path = Path(tmp.name)
        
        try:
            with open(tmp_path, "rb") as f:
                # 使用无效的Content-Type
                files = {"file": ("test.txt", f, "invalid/content-type")}
                response = test_client.post("/upload", files=files)
            
            # 期望返回400错误（不支持的文件类型）
            assert response.status_code == 400
            result = response.json()
            assert "不支持的文件类型" in result.get("detail", "")
            print(f"✅ UP-BV-05通过: 无效Content-Type返回400错误")
            
        finally:
            tmp_path.unlink(missing_ok=True)
    
    def test_search_top_k_boundary_minimum(self, test_client: TestClient):
        """SR-BV-01: top_k边界-最小值(1)"""
        response = test_client.get("/search?q=质量方针&top_k=1")
        
        # 期望返回200，结果数量≤1
        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)
        assert len(results) <= 1
        
        if len(results) > 0:
            # 验证结果格式
            result = results[0]
            assert "text" in result
            assert "source" in result
            assert "tags" in result
            assert "score" in result
            assert 0 <= result["score"] <= 1
        
        print(f"✅ SR-BV-01通过: top_k=1返回{len(results)}个结果")
    
    def test_search_top_k_boundary_maximum(self, test_client: TestClient):
        """SR-BV-02: top_k边界-最大值(100)"""
        response = test_client.get("/search?q=质量方针&top_k=100")
        
        # 期望返回200，结果数量≤100
        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)
        assert len(results) <= 100
        
        # 验证所有结果的格式
        for result in results:
            assert "text" in result
            assert "source" in result
            assert "tags" in result
            assert "score" in result
            assert 0 <= result["score"] <= 1
        
        print(f"✅ SR-BV-02通过: top_k=100返回{len(results)}个结果")
    
    def test_search_top_k_boundary_over_maximum(self, test_client: TestClient):
        """SR-BV-03: top_k边界-超过最大值(101)"""
        response = test_client.get("/search?q=质量方针&top_k=101")
        
        # 期望返回422验证错误
        assert response.status_code == 422
        print(f"✅ SR-BV-03通过: top_k=101返回422错误")
    
    def test_search_top_k_boundary_zero(self, test_client: TestClient):
        """SR-BV-04: top_k边界-零值"""
        response = test_client.get("/search?q=质量方针&top_k=0")
        
        # 期望返回422验证错误
        assert response.status_code == 422
        print(f"✅ SR-BV-04通过: top_k=0返回422错误")
    
    def test_search_top_k_boundary_negative(self, test_client: TestClient):
        """SR-BV-05: top_k边界-负值"""
        response = test_client.get("/search?q=质量方针&top_k=-1")
        
        # 期望返回422验证错误
        assert response.status_code == 422
        print(f"✅ SR-BV-05通过: top_k=-1返回422错误")
    
    def test_task_id_boundary_invalid_format(self, test_client: TestClient):
        """TS-BV-01: 任务ID边界-无效格式"""
        invalid_task_ids = [
            "",  # 空字符串
            "invalid-format",  # 非UUID格式
            "123",  # 过短
            "a" * 100,  # 过长
            "not-a-uuid"  # 明显无效
        ]
        
        for task_id in invalid_task_ids:
            response = test_client.get(f"/upload/status/{task_id}")
            
            # 期望返回404（任务不存在）
            assert response.status_code == 404
            result = response.json()
            assert "任务不存在" in result.get("detail", "")
        
        print(f"✅ TS-BV-01通过: 验证了{len(invalid_task_ids)}个无效任务ID格式")
    
    def test_ask_question_length_boundary_short(self, test_client: TestClient):
        """AS-BV-01: 问题长度边界-最短"""
        short_questions = ["是", "什么", "如何"]
        
        for question in short_questions:
            response = test_client.post("/ask", json={"question": question})
            
            # 期望返回200，系统应该能处理短问题
            assert response.status_code == 200
            result = response.json()
            assert "answer" in result
            assert "sources" in result
            assert isinstance(result["answer"], str)
            assert len(result["answer"]) > 0
        
        print(f"✅ AS-BV-01通过: 验证了{len(short_questions)}个短问题")
    
    def test_concurrent_upload_boundary(self, test_client: TestClient):
        """PF-BV-01: 并发上传边界测试"""
        import concurrent.futures
        import threading
        
        # 创建多个测试文件
        test_files = []
        for i in range(5):  # 5个并发
            pdf_content = f"%PDF-1.4\n测试内容{i}".encode()
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(pdf_content)
                test_files.append(Path(tmp.name))
        
        try:
            results = []
            
            def upload_file(file_path: Path, index: int):
                with open(file_path, "rb") as f:
                    files = {"file": (f"test_{index}.pdf", f, "application/pdf")}
                    response = test_client.post("/upload", files=files)
                    return response.status_code, response.json()
            
            # 并发上传
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(upload_file, test_files[i], i) for i in range(5)]
                
                for future in concurrent.futures.as_completed(futures):
                    try:
                        status_code, result = future.result()
                        results.append((status_code, result))
                    except Exception as e:
                        results.append((500, {"error": str(e)}))
            
            # 验证所有上传都成功
            success_count = sum(1 for status, _ in results if status == 200)
            assert success_count == 5, f"期望5个成功，实际{success_count}个"
            
            print(f"✅ PF-BV-01通过: 5个并发上传全部成功")
            
        finally:
            # 清理临时文件
            for file_path in test_files:
                file_path.unlink(missing_ok=True)


class TestBoundaryValuesAdvanced:
    """高级边界值测试"""
    
    def test_file_content_boundary_empty_pdf(self, test_client: TestClient):
        """高级边界: 空的PDF结构"""
        # 创建只有PDF头但没有内容的文件
        pdf_header = b"%PDF-1.4\n"
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_header)
            tmp_path = Path(tmp.name)
        
        try:
            with open(tmp_path, "rb") as f:
                files = {"file": ("empty_structure.pdf", f, "application/pdf")}
                response = test_client.post("/upload", files=files)
            
            # 系统应该能处理这种边界情况
            assert response.status_code in [200, 400]
            print(f"✅ 空PDF结构测试通过: 返回{response.status_code}")
            
        finally:
            tmp_path.unlink(missing_ok=True)
    
    def test_unicode_boundary_search(self, test_client: TestClient):
        """Unicode字符边界测试"""
        unicode_queries = [
            "质量方针",  # 中文
            "Quality Policy",  # 英文
            "品質方針",  # 日文
            "정책",  # 韩文
            "نموذج",  # 阿拉伯文
            "🚀📊🔍",  # Emoji
            "质量方针 123 ABC 🚀"  # 混合
        ]
        
        for query in unicode_queries:
            response = test_client.get(f"/search?q={query}&top_k=5")
            
            # 期望能处理各种Unicode字符
            assert response.status_code == 200
            results = response.json()
            assert isinstance(results, list)
            
            print(f"✅ Unicode测试通过: '{query[:20]}...' 返回{len(results)}个结果")
    
    def test_special_characters_boundary(self, test_client: TestClient):
        """特殊字符边界测试"""
        special_chars = [
            "!@#$%^&*()",  # 特殊符号
            "质量方针\"管理\"",  # 引号
            "质量'方针'",  # 单引号
            "质量[方针]",  # 方括号
            "质量{方针}",  # 花括号
            "质量(方针)",  # 圆括号
            "质量方针\n管理",  # 换行符
            "质量方针\t管理"  # 制表符
        ]
        
        for query in special_chars:
            response = test_client.get(f"/search?q={query}&top_k=3")
            
            # 系统应该能处理特殊字符，不会崩溃
            assert response.status_code == 200
            print(f"✅ 特殊字符测试通过: '{query[:20]}...'")


if __name__ == "__main__":
    # 运行边界值测试
    pytest.main([__file__, "-v", "-s"])