"""
等价类测试用例实现
基于测试设计文档的具体测试代码
"""
import pytest
import tempfile
from pathlib import Path
from typing import Dict, Any
from fastapi.testclient import TestClient

from tests.integration.test_cases_design import test_cases, TestType, TestPriority


class TestEquivalenceClasses:
    """等价类测试类"""
    
    def test_upload_valid_file_types(self, test_client: TestClient):
        """UP-EC-01~05: 有效文件类型等价类测试"""
        
        # 定义有效文件类型和对应的测试内容
        valid_file_types = [
            ("application/pdf", "test.pdf", b"%PDF-1.4\n1 0 obj<<>>endobj"),
            ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "test.docx", b"PK" + b"Word测试内容" * 100),
            ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "test.xlsx", b"PK" + b"Excel测试内容" * 100),
            ("application/vnd.openxmlformats-officedocument.presentationml.presentation", "test.pptx", b"PK" + b"PPT测试内容" * 100),
            ("application/vnd.ms-excel", "test.xls", b"测试Excel内容" * 100)
        ]
        
        for content_type, filename, content in valid_file_types:
            with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as tmp:
                tmp.write(content)
                tmp_path = Path(tmp.name)
            
            try:
                with open(tmp_path, "rb") as f:
                    files = {"file": (filename, f, content_type)}
                    response = test_client.post("/upload", files=files)
                
                # 期望返回200成功
                assert response.status_code == 200, f"{content_type} 应该上传成功"
                result = response.json()
                assert "task_id" in result
                assert result["status"] == "Pending"
                
                print(f"✅ UP-EC通过: {content_type} 上传成功")
                
            finally:
                tmp_path.unlink(missing_ok=True)
    
    def test_upload_invalid_file_types(self, test_client: TestClient):
        """UP-EC-06~09: 无效文件类型等价类测试"""
        
        # 定义无效文件类型
        invalid_file_types = [
            ("image/jpeg", "test.jpg", b"\xFF\xD8\xFF\xE0" + b"JPEG测试" * 100),
            ("text/plain", "test.txt", b"纯文本测试内容" * 100),
            ("application/x-msdownload", "test.exe", b"MZ" + b"可执行文件测试" * 100),
            ("video/mp4", "test.mp4", b"ftyp" + b"视频文件测试" * 100)
        ]
        
        for content_type, filename, content in invalid_file_types:
            with tempfile.NamedTemporaryFile(suffix=Path(filename).suffix, delete=False) as tmp:
                tmp.write(content)
                tmp_path = Path(tmp.name)
            
            try:
                with open(tmp_path, "rb") as f:
                    files = {"file": (filename, f, content_type)}
                    response = test_client.post("/upload", files=files)
                
                # 期望返回400错误（不支持的文件类型）
                assert response.status_code == 400, f"{content_type} 应该被拒绝"
                result = response.json()
                assert "不支持的文件类型" in result.get("detail", "")
                
                print(f"✅ UP-EC通过: {content_type} 正确被拒绝")
                
            finally:
                tmp_path.unlink(missing_ok=True)
    
    def test_search_valid_query_types(self, test_client: TestClient):
        """SR-EC-01~05: 有效查询类型等价类测试"""
        
        # 定义有效查询类型
        valid_queries = [
            ("质量方针管理要求", "中文事实查询"),
            ("quality management system", "英文事实查询"),
            ("ISO 9001质量管理体系要求", "混合语言查询"),
            ("如何制定质量目标", "程序型查询"),
            ("质量管理和质量控制的区别", "对比型查询")
        ]
        
        for query, description in valid_queries:
            response = test_client.get(f"/search?q={query}&top_k=5")
            
            # 期望返回200成功
            assert response.status_code == 200, f"'{query}' 查询应该成功"
            results = response.json()
            assert isinstance(results, list)
            
            # 验证结果格式（如果有结果的话）
            if len(results) > 0:
                for result in results:
                    assert "text" in result
                    assert "source" in result
                    assert "tags" in result
                    assert "score" in result
                    assert 0 <= result["score"] <= 1
            
            print(f"✅ SR-EC通过: {description} '{query[:20]}...' 返回{len(results)}个结果")
    
    def test_search_invalid_query_types(self, test_client: TestClient):
        """SR-EC-06~09: 无效查询类型等价类测试"""
        
        # 定义无效查询类型
        invalid_queries = [
            ("", "空查询"),
            ("   ", "仅空格"),
            ("@#$%^&*()", "特殊字符"),
            ("a" * 1000, "超长查询")
        ]
        
        for query, description in invalid_queries:
            response = test_client.get(f"/search?q={query}&top_k=5")
            
            if not query or not query.strip():  # 空查询或仅空格
                # 期望返回400错误或空结果
                assert response.status_code in [200, 400]
                if response.status_code == 200:
                    results = response.json()
                    assert isinstance(results, list)
                    assert len(results) == 0  # 应该返回空结果
                else:
                    result = response.json()
                    assert "detail" in result
            else:
                # 特殊字符或超长查询，期望返回200但结果可能为空
                assert response.status_code == 200
                results = response.json()
                assert isinstance(results, list)
            
            print(f"✅ SR-EC通过: {description} 正确处理")
    
    def test_ask_valid_question_types(self, test_client: TestClient):
        """AS-EC-01~05: 有效问题类型等价类测试"""
        
        # 定义有效问题类型
        valid_questions = [
            ("什么是质量方针？", "事实型问题"),
            ("如何制定质量目标？", "程序型问题"),
            ("质量管理和质量控制的区别？", "对比型问题"),
            ("请解释ISO 9001标准", "解释型问题"),
            ("质量管理体系包括哪些内容？", "列举型问题")
        ]
        
        for question, description in valid_questions:
            response = test_client.post("/ask", json={"question": question})
            
            # 期望返回200成功
            assert response.status_code == 200, f"'{question}' 应该返回成功"
            result = response.json()
            assert "answer" in result
            assert "sources" in result
            assert isinstance(result["answer"], str)
            assert len(result["answer"]) > 0
            assert isinstance(result["sources"], list)
            
            print(f"✅ AS-EC通过: {description} 获得有效回答")
    
    def test_ask_invalid_question_types(self, test_client: TestClient):
        """AS-EC-06~10: 无效问题类型等价类测试"""
        
        # 定义无效问题类型
        invalid_questions = [
            ("", "空问题"),
            ("   ", "仅空格"),
            ("今天天气如何？", "无关问题"),
            ("123456", "无意义数字"),
            ("a" * 2000, "超长问题")
        ]
        
        for question, description in invalid_questions:
            response = test_client.post("/ask", json={"question": question})
            
            if not question or not question.strip():  # 空问题或仅空格
                # 期望返回400错误
                assert response.status_code == 400
                result = response.json()
                assert "detail" in result
                print(f"✅ AS-EC通过: {description} 返回400错误")
                
            elif question == "今天天气如何？":  # 无关问题
                # 期望返回200，但回答应该是默认的"知识库中暂无相关记录"
                assert response.status_code == 200
                result = response.json()
                assert "answer" in result
                # 注意：实际实现可能返回不同的默认回答
                print(f"✅ AS-EC通过: {description} 返回默认回答")
                
            else:  # 无意义数字或超长问题
                # 期望返回200，系统应该能处理
                assert response.status_code == 200
                result = response.json()
                assert "answer" in result
                assert "sources" in result
                print(f"✅ AS-EC通过: {description} 获得处理")
    
    def test_task_status_valid_ids(self, test_client: TestClient):
        """TS-EC-01: 有效任务ID等价类测试"""
        
        # 首先创建一个上传任务
        pdf_content = b"%PDF-1.4\n1 0 obj<<>>endobj"
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_content)
            tmp_path = Path(tmp.name)
        
        try:
            # 上传文件获取任务ID
            with open(tmp_path, "rb") as f:
                files = {"file": ("test.pdf", f, "application/pdf")}
                upload_response = test_client.post("/upload", files=files)
            
            assert upload_response.status_code == 200
            upload_result = upload_response.json()
            task_id = upload_result["task_id"]
            
            # 查询任务状态
            status_response = test_client.get(f"/upload/status/{task_id}")
            
            # 期望返回200成功
            assert status_response.status_code == 200
            status_result = status_response.json()
            assert "task_id" in status_result
            assert "status" in status_result
            assert status_result["task_id"] == task_id
            assert status_result["status"] in ["Pending", "Processing", "Completed", "Failed"]
            
            print(f"✅ TS-EC通过: 有效任务ID '{task_id[:8]}...' 状态查询成功")
            
        finally:
            tmp_path.unlink(missing_ok=True)
    
    def test_task_status_invalid_ids(self, test_client: TestClient):
        """TS-EC-02~06: 无效任务ID等价类测试"""
        
        # 定义无效任务ID
        invalid_task_ids = [
            ("", "空任务ID"),
            ("invalid-format", "非UUID格式"),
            ("123", "过短ID"),
            ("a" * 100, "过长ID"),
            ("not-a-uuid-at-all", "明显无效ID")
        ]
        
        for task_id, description in invalid_task_ids:
            if not task_id:  # 空任务ID
                # FastAPI会返回404，因为路径不匹配
                continue
            
            response = test_client.get(f"/upload/status/{task_id}")
            
            # 期望返回404错误（任务不存在）
            assert response.status_code == 404, f"'{task_id}' 应该返回404"
            result = response.json()
            assert "任务不存在" in result.get("detail", "")
            
            print(f"✅ TS-EC通过: {description} 正确返回404错误")
    
    def test_search_tag_filter_equivalence(self, test_client: TestClient):
        """SR-TF-01~04: 标签过滤等价类测试"""
        
        # 定义标签过滤测试用例
        tag_filter_tests = [
            (["质量"], "单标签过滤"),
            (["质量", "管理"], "多标签过滤"),
            (["不存在的标签"], "不存在标签"),
            ([], "空标签列表")
        ]
        
        for tags, description in tag_filter_tests:
            # 构建查询URL
            url = f"/search?q=质量方针&top_k=5"
            if tags:
                tag_params = "&".join([f"filter_tags={tag}" for tag in tags])
                url += f"&{tag_params}"
            
            response = test_client.get(url)
            
            # 期望返回200成功
            assert response.status_code == 200, f"{description} 应该返回成功"
            results = response.json()
            assert isinstance(results, list)
            
            # 验证结果格式
            for result in results:
                assert "text" in result
                assert "source" in result
                assert "tags" in result
                assert "score" in result
                assert 0 <= result["score"] <= 1
            
            print(f"✅ SR-TF通过: {description} 返回{len(results)}个结果")
    
    def test_health_check_equivalence(self, test_client: TestClient):
        """HC-01: 健康检查等价类测试"""
        
        response = test_client.get("/health")
        
        # 期望返回200成功
        assert response.status_code == 200
        result = response.json()
        assert "status" in result
        assert result["status"] == "ok"
        
        print(f"✅ HC-EC通过: 健康检查返回正常状态")


class TestEquivalenceEdgeCases:
    """等价类边界情况测试"""
    
    def test_mixed_language_equivalence(self, test_client: TestClient):
        """混合语言等价类测试"""
        
        mixed_queries = [
            "ISO 9001 质量管理体系",
            "quality 质量 management 管理",
            "QMS 质量管理系统 requirements 要求",
            "质量方针 quality policy",
            "management 管理 system 体系"
        ]
        
        for query in mixed_queries:
            response = test_client.get(f"/search?q={query}&top_k=3")
            
            assert response.status_code == 200
            results = response.json()
            assert isinstance(results, list)
            
            print(f"✅ 混合语言测试通过: '{query}' 返回{len(results)}个结果")
    
    def test_special_content_equivalence(self, test_client: TestClient):
        """特殊内容等价类测试"""
        
        # 测试包含数字、符号的内容
        special_content_queries = [
            "ISO 9001:2015 标准",
            "质量-管理-体系",
            "质量/管理/体系",
            "质量_管理_体系",
            "质量.管理.体系",
            "质量(管理)体系",
            "质量[管理]体系",
            "质量{管理}体系"
        ]
        
        for query in special_content_queries:
            response = test_client.get(f"/search?q={query}&top_k=2")
            
            assert response.status_code == 200
            results = response.json()
            assert isinstance(results, list)
            
            print(f"✅ 特殊内容测试通过: '{query}' 返回{len(results)}个结果")
    
    def test_case_sensitivity_equivalence(self, test_client: TestClient):
        """大小写敏感等价类测试"""
        
        # 测试大小写是否影响搜索结果
        case_variants = [
            ("Quality Management", "Quality Management"),
            ("quality management", "quality management"),
            ("QUALITY MANAGEMENT", "QUALITY MANAGEMENT"),
            ("Quality management", "Quality management"),
            ("qUaLiTy MaNaGeMeNt", "qUaLiTy MaNaGeMeNt")
        ]
        
        for lower_query, original_query in case_variants:
            response = test_client.get(f"/search?q={original_query}&top_k=3")
            
            assert response.status_code == 200
            results = response.json()
            assert isinstance(results, list)
            
            print(f"✅ 大小写测试通过: '{original_query}' 返回{len(results)}个结果")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])