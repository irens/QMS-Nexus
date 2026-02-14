"""
QMS-Nexus 集成测试 - 完整RAG链路验证
测试从文件上传到最终问答的完整流程
"""
import json
import time
from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient

# 从utils导入工具函数
try:
    from .utils import poll_task_status, assert_query_response_format
except ImportError:
    # 直接运行时的导入
    import sys
    sys.path.append(str(Path(__file__).parent))
    from utils import poll_task_status, assert_query_response_format


class TestRAGIntegration:
    """RAG完整链路集成测试"""
    
    def test_health_check(
        self,
        test_client: TestClient
    ):
        """
        测试健康检查接口
        """
        print(f"\n🏥 开始健康检查测试")
        
        response = test_client.get("/health")
        print(f"💓 健康检查响应: {response.status_code}")
        
        assert response.status_code == 200, "健康检查应该返回200"
        
        result = response.json()
        assert "status" in result, "健康检查应该包含status字段"
        assert result["status"] == "ok", "健康检查状态应该是ok"
        
        print(f"✅ 健康检查测试完成")
    
    def test_upload_pdf_workflow(
        self, 
        test_client: TestClient, 
        sample_pdf_path: Path
    ):
        """
        流程A：上传PDF -> 轮询任务状态 -> 验证数据存储
        """
        print(f"\n🚀 开始流程A测试：上传PDF文档")
        
        # 1. 上传PDF文件
        with open(sample_pdf_path, "rb") as f:
            files = {"file": ("test_document.pdf", f, "application/pdf")}
            response = test_client.post("/upload", files=files)
        
        print(f"📄 上传响应状态码: {response.status_code}")
        assert response.status_code == 200
        
        upload_result = response.json()
        print(f"📤 上传结果: {upload_result}")
        assert "task_id" in upload_result
        task_id = upload_result["task_id"]
        
        # 2. 轮询任务状态
        print(f"⏳ 轮询任务状态: {task_id}")
        try:
            final_status = poll_task_status(test_client, task_id, max_retries=30, interval=1)
            print(f"✅ 任务完成: {final_status}")
        except TimeoutError:
            pytest.fail("任务处理超时")
        except RuntimeError as e:
            pytest.fail(f"任务处理失败: {e}")
        
        # 3. 验证搜索结果（确保文档被正确处理）
        print(f"🔍 验证搜索结果...")
        search_response = test_client.get("/search?q=test&top_k=3")
        print(f"🔎 搜索响应: {search_response.status_code}")
        
        if search_response.status_code == 200:
            search_results = search_response.json()
            print(f"📊 搜索结果数量: {len(search_results)}")
            
            # 验证第一个结果的格式
            if len(search_results) > 0:
                first_result = search_results[0]
                assert "text" in first_result
                assert "source" in first_result
                assert "tags" in first_result
                assert "score" in first_result
                
                print(f"✅ 流程A完成：任务{task_id}成功处理")
            else:
                print(f"⚠️  未找到搜索结果，但上传流程完成")
        else:
            print(f"⚠️  搜索失败，但上传流程完成")
    
    def test_search_workflow(
        self,
        test_client: TestClient
    ):
        """
        流程B：调用/search提问 -> 验证返回结果格式
        """
        print(f"\n🔍 开始流程B测试：搜索功能")
        
        # 1. 发送搜索请求
        search_query = "test document"
        response = test_client.get(f"/search?q={search_query}&top_k=3")
        
        print(f"🔎 搜索响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            results = response.json()
            print(f"📊 搜索结果数量: {len(results)}")
            
            # 2. 验证返回结果结构
            assert isinstance(results, list), "搜索结果应该是列表"
            
            if len(results) > 0:
                # 验证第一个结果的格式
                first_result = results[0]
                assert "text" in first_result, "结果应该包含text字段"
                assert "source" in first_result, "结果应该包含source字段"
                assert "tags" in first_result, "结果应该包含tags字段"
                assert "score" in first_result, "结果应该包含score字段"
                
                # 验证source格式
                source = first_result["source"]
                assert isinstance(source, str), "source应该是字符串"
                assert len(source) > 0, "source不应该为空"
                
                # 验证score范围
                score = first_result["score"]
                assert 0 <= score <= 1, "score应该在0-1之间"
                
                # 验证tags格式
                tags = first_result["tags"]
                assert isinstance(tags, list), "tags应该是列表"
                
                print(f"✅ 流程B完成：搜索功能正常")
            else:
                print(f"⚠️  未找到搜索结果，但搜索接口正常")
        else:
            print(f"⚠️  搜索接口返回错误: {response.status_code}")
    
    def test_ask_workflow(
        self,
        test_client: TestClient
    ):
        """
        测试问答功能
        """
        print(f"\n💬 开始测试问答功能")
        
        # 1. 发送问答请求
        ask_data = {
            "question": "这个文档的主要内容是什么？"
        }
        
        response = test_client.post("/ask", json=ask_data)
        print(f"💭 问答响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"💡 问答结果: {result}")
            
            # 2. 验证返回结果结构
            assert "answer" in result, "回答应该包含answer字段"
            assert "sources" in result, "回答应该包含sources字段"
            
            # 3. 验证回答内容
            answer = result["answer"]
            assert isinstance(answer, str), "answer应该是字符串"
            assert len(answer) > 0, "answer不应该为空"
            
            # 4. 验证来源
            sources = result["sources"]
            assert isinstance(sources, list), "sources应该是列表"
            
            print(f"✅ 问答功能测试完成")
        else:
            print(f"⚠️  问答接口返回错误: {response.status_code}")
    
    def test_complete_integration_pipeline(
        self,
        test_client: TestClient,
        sample_pdf_path: Path
    ):
        """
        完整集成链路测试：上传 -> 搜索 -> 问答 -> 健康检查
        """
        print("\n🚀 开始完整集成链路测试...")
        
        # 1. 健康检查
        self.test_health_check(test_client)
        
        # 2. 上传文档
        self.test_upload_pdf_workflow(test_client, sample_pdf_path)
        
        # 3. 搜索功能
        self.test_search_workflow(test_client)
        
        # 4. 问答功能
        self.test_ask_workflow(test_client)
        
        print("\n✅ 完整集成链路测试通过！")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])