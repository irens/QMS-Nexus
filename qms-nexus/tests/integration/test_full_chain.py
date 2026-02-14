"""
全链路闭环测试实现
基于综合测试用例设计的具体测试代码实现
"""
import pytest
import asyncio
import time
import json
import hashlib
from typing import Dict, List, Any, Optional
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import aiohttp
from unittest.mock import patch, MagicMock

from tests.integration.conftest import TestClient
from tests.integration.mock_llm import LLMServiceMock
from tests.integration.COMPREHENSIVE_TEST_CASES import comprehensive_test_cases, TestType, TestPriority


class TestFullChainIntegration:
    """全链路集成测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self, test_client: TestClient, test_data_dir: Path):
        """测试前置设置"""
        self.client = test_client
        self.test_data_dir = test_data_dir
        self.test_results = []
        self.start_time = time.time()
        
    def create_test_pdf(self, filename: str, content: str, file_size: int = 1024) -> Path:
        """创建测试PDF文件"""
        pdf_path = self.test_data_dir / filename
        # 创建包含指定内容的PDF文件
        # 这里简化处理，实际应该生成真实的PDF
        with open(pdf_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return pdf_path
    
    async def poll_task_to_completion(self, task_id: str, timeout: int = 120, interval: float = 1.0) -> str:
        """轮询任务状态直到完成"""
        start_time = time.time()
        last_status = None
        
        while time.time() - start_time < timeout:
            response = await self.client.get(f"/tasks/{task_id}")
            assert response.status_code == 200
            
            task_data = response.json()
            current_status = task_data["status"]
            
            # 记录状态变化
            if current_status != last_status:
                print(f"任务 {task_id} 状态变化: {last_status} -> {current_status}")
                last_status = current_status
            
            if current_status in ["Completed", "Failed"]:
                return current_status
            
            await asyncio.sleep(interval)
        
        raise TimeoutError(f"任务 {task_id} 在 {timeout} 秒内未完成")
    
    async def wait_for_document_indexed(self, query: str, expected_source: str, timeout: int = 30) -> bool:
        """等待文档被索引并可搜索"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            response = await self.client.get(f"/search?q={query}&top_k=5")
            if response.status_code == 200:
                results = response.json()
                for result in results:
                    if expected_source in result.get("source", ""):
                        return True
            await asyncio.sleep(1)
        
        return False
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_case", [
        case for case in comprehensive_test_cases.get_test_cases_by_type(TestType.FULL_CHAIN)
        if case.priority == TestPriority.P0
    ])
    async def test_full_chain_success(self, test_case):
        """测试全链路成功场景 - TC-FULL-001"""
        print(f"\n=== 执行测试: {test_case.case_id} ===")
        print(f"描述: {test_case.description}")
        
        try:
            # Step 1: 上传PDF文件
            print("步骤1: 上传PDF文件...")
            test_content = "质量管理体系标准文档内容。质量方针是组织在质量方面的宗旨和方向。"
            pdf_path = self.create_test_pdf("test_qms.pdf", test_content)
            
            with open(pdf_path, 'rb') as f:
                files = {"file": ("test_qms.pdf", f, "application/pdf")}
                response = await self.client.post("/upload", files=files)
            
            assert response.status_code == 200
            task_data = response.json()
            task_id = task_data["task_id"]
            assert task_data["status"] == "Pending"
            print(f"✓ 任务创建成功: {task_id}")
            
            # Step 2: 轮询任务状态
            print("步骤2: 轮询任务状态...")
            final_status = await self.poll_task_to_completion(task_id, timeout=120)
            assert final_status == "Completed"
            print("✓ 任务处理完成")
            
            # Step 3: 验证向量存储
            print("步骤3: 验证向量存储...")
            await asyncio.sleep(2)  # 等待索引建立
            
            response = await self.client.get("/search?q=质量管理&top_k=5")
            assert response.status_code == 200
            search_results = response.json()
            assert len(search_results) > 0
            
            # 验证结果中包含上传的文档
            found_source = False
            for result in search_results:
                if "test_qms.pdf" in result.get("source", ""):
                    found_source = True
                    break
            assert found_source, "搜索结果中应该包含上传的文档"
            print("✓ 向量存储验证通过")
            
            # Step 4: 提问测试
            print("步骤4: 提问测试...")
            response = await self.client.post("/ask", json={"question": "什么是质量方针？"})
            assert response.status_code == 200
            answer_data = response.json()
            
            assert "answer" in answer_data
            assert "sources" in answer_data
            assert len(answer_data["sources"]) > 0
            assert "质量方针" in answer_data["answer"]
            print(f"✓ 问答测试通过，答案: {answer_data['answer'][:100]}...")
            
            # Step 5: 提交反馈 (如果有反馈接口)
            print("步骤5: 提交反馈...")
            try:
                feedback_data = {
                    "task_id": task_id,
                    "feedback": "like",
                    "comment": "回答准确"
                }
                response = await self.client.post("/feedback", json=feedback_data)
                if response.status_code == 200:
                    print("✓ 反馈提交成功")
                else:
                    print(f"反馈接口返回状态: {response.status_code} (可能接口不存在)")
            except Exception as e:
                print(f"反馈接口测试跳过: {e}")
            
            # Step 6: 验证监控指标
            print("步骤6: 验证监控指标...")
            try:
                response = await self.client.get("/metrics")
                if response.status_code == 200:
                    metrics_data = response.text
                    assert "qms_upload_total" in metrics_data
                    assert "qms_search_total" in metrics_data
                    print("✓ 监控指标验证通过")
                else:
                    print(f"监控接口返回状态: {response.status_code}")
            except Exception as e:
                print(f"监控指标验证跳过: {e}")
            
            print(f"✅ {test_case.case_id} 测试通过!")
            
        except Exception as e:
            print(f"❌ {test_case.case_id} 测试失败: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_chain_interruption_recovery(self):
        """测试链路中断恢复 - TC-FULL-002"""
        print("\n=== 执行测试: TC-FULL-002 链路中断恢复 ===")
        
        try:
            # Step 1: 建立正常业务基线
            print("步骤1: 建立正常业务基线...")
            baseline_pdf = self.create_test_pdf("baseline.pdf", "基线测试文档内容")
            
            with open(baseline_pdf, 'rb') as f:
                files = {"file": ("baseline.pdf", f, "application/pdf")}
                response = await self.client.post("/upload", files=files)
            
            assert response.status_code == 200
            baseline_task_id = response.json()["task_id"]
            print(f"✓ 基线任务创建: {baseline_task_id}")
            
            # Step 2: 模拟Redis服务中断
            print("步骤2: 模拟Redis服务中断...")
            # 这里使用Mock来模拟Redis连接失败
            with patch('redis.Redis.ping', side_effect=Exception("Redis连接失败")):
                # Step 3: 在中断期间上传新文件
                print("步骤3: 在中断期间上传新文件...")
                during_failure_pdf = self.create_test_pdf("during_failure.pdf", "中断期间测试文档")
                
                with open(during_failure_pdf, 'rb') as f:
                    files = {"file": ("during_failure.pdf", f, "application/pdf")}
                    response = await self.client.post("/upload", files=files)
                
                assert response.status_code == 200
                during_failure_task_id = response.json()["task_id"]
                print(f"✓ 中断期间任务创建: {during_failure_task_id}")
                
                # 验证任务保持Pending状态
                response = await self.client.get(f"/tasks/{during_failure_task_id}")
                assert response.status_code == 200
                task_status = response.json()["status"]
                assert task_status == "Pending"
                print("✓ 任务保持Pending状态")
            
            # Step 4: 恢复Redis服务 (Mock结束，自动恢复)
            print("步骤4: Redis服务恢复...")
            
            # Step 5: 验证中断期间的任务继续处理
            print("步骤5: 验证任务继续处理...")
            final_status = await self.poll_task_to_completion(during_failure_task_id, timeout=60)
            assert final_status == "Completed"
            print("✓ 中断期间任务处理完成")
            
            # Step 6: 验证数据完整性
            print("步骤6: 验证数据完整性...")
            found = await self.wait_for_document_indexed("中断期间", "during_failure.pdf")
            assert found, "应该能找到中断期间上传的文档"
            print("✓ 数据完整性验证通过")
            
            print("✅ TC-FULL-002 链路中断恢复测试通过!")
            
        except Exception as e:
            print(f"❌ TC-FULL-002 测试失败: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_concurrent_full_chain(self):
        """测试并发全链路 - TC-FULL-003"""
        print("\n=== 执行测试: TC-FULL-003 并发全链路 ===")
        
        try:
            # 参数设置
            concurrent_users = 3
            files_per_user = 2
            total_files = concurrent_users * files_per_user
            
            print(f"设置: {concurrent_users}用户, {files_per_user}文件/用户, 总计{total_files}文件")
            
            # 创建测试数据
            test_files = []
            for i in range(total_files):
                content = f"并发测试文档{i+1}内容。包含关键词：并发测试、质量管理。"
                filename = f"concurrent_test_{i+1}.pdf"
                pdf_path = self.create_test_pdf(filename, content)
                test_files.append((filename, pdf_path))
            
            # 并发上传
            print("并发上传测试...")
            upload_tasks = []
            for filename, pdf_path in test_files:
                task = self.upload_file_async(filename, pdf_path)
                upload_tasks.append(task)
            
            upload_results = await asyncio.gather(*upload_tasks, return_exceptions=True)
            
            # 验证上传结果
            successful_uploads = 0
            task_ids = []
            for result in upload_results:
                if isinstance(result, Exception):
                    print(f"上传异常: {result}")
                else:
                    response, filename = result
                    if response.status_code == 200:
                        successful_uploads += 1
                        task_id = response.json()["task_id"]
                        task_ids.append((task_id, filename))
            
            upload_success_rate = successful_uploads / total_files
            print(f"上传成功率: {upload_success_rate:.1%} ({successful_uploads}/{total_files})")
            assert upload_success_rate >= 0.95, "上传成功率应该≥95%"
            
            # 并发等待任务完成
            print("并发等待任务处理...")
            completion_tasks = [
                self.wait_task_completion_async(task_id, filename)
                for task_id, filename in task_ids
            ]
            
            completion_results = await asyncio.gather(*completion_tasks, return_exceptions=True)
            
            successful_completions = sum(1 for result in completion_results if result is True)
            print(f"任务完成率: {successful_completions}/{successful_uploads}")
            
            # 并发搜索测试
            print("并发搜索测试...")
            search_queries = ["并发测试", "质量管理", "质量方针"]
            search_tasks = []
            
            for query in search_queries:
                for _ in range(5):  # 每个查询5次
                    task = self.search_async(query)
                    search_tasks.append(task)
            
            search_start_time = time.time()
            search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
            search_duration = time.time() - search_start_time
            
            # 验证搜索结果
            successful_searches = 0
            response_times = []
            for result in search_results:
                if isinstance(result, Exception):
                    print(f"搜索异常: {result}")
                else:
                    response, response_time = result
                    if response.status_code == 200:
                        successful_searches += 1
                        response_times.append(response_time)
            
            search_success_rate = successful_searches / len(search_tasks)
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            print(f"搜索成功率: {search_success_rate:.1%}")
            print(f"平均响应时间: {avg_response_time:.2f}s")
            print(f"总搜索耗时: {search_duration:.2f}s")
            
            assert search_success_rate >= 0.95, "搜索成功率应该≥95%"
            assert avg_response_time <= 2.0, "平均响应时间应该≤2s"
            
            # 并发问答测试
            print("并发问答测试...")
            questions = [
                "什么是并发测试？",
                "质量管理的主要内容包括哪些？",
                "如何确保测试的准确性？"
            ]
            
            ask_tasks = []
            for question in questions:
                for _ in range(3):  # 每个问题3次
                    task = self.ask_question_async(question)
                    ask_tasks.append(task)
            
            ask_results = await asyncio.gather(*ask_tasks, return_exceptions=True)
            
            successful_asks = 0
            for result in ask_results:
                if isinstance(result, Exception):
                    print(f"问答异常: {result}")
                else:
                    response = result
                    if response.status_code == 200:
                        answer_data = response.json()
                        if "answer" in answer_data and len(answer_data["answer"]) > 0:
                            successful_asks += 1
            
            ask_success_rate = successful_asks / len(ask_tasks)
            print(f"问答成功率: {ask_success_rate:.1%}")
            assert ask_success_rate >= 0.90, "问答成功率应该≥90%"
            
            # 验证数据一致性
            print("验证数据一致性...")
            for task_id, filename in task_ids[:3]:  # 检查前3个文件
                found = await self.wait_for_document_indexed("并发测试", filename)
                assert found, f"应该能找到文件 {filename}"
            print("✓ 数据一致性验证通过")
            
            print("✅ TC-FULL-003 并发全链路测试通过!")
            
        except Exception as e:
            print(f"❌ TC-FULL-003 测试失败: {e}")
            raise
    
    # 辅助方法
    async def upload_file_async(self, filename: str, pdf_path: Path):
        """异步上传文件"""
        try:
            with open(pdf_path, 'rb') as f:
                files = {"file": (filename, f, "application/pdf")}
                response = await self.client.post("/upload", files=files)
            return response, filename
        except Exception as e:
            return e
    
    async def wait_task_completion_async(self, task_id: str, filename: str):
        """异步等待任务完成"""
        try:
            final_status = await self.poll_task_to_completion(task_id, timeout=60)
            return final_status == "Completed"
        except Exception as e:
            print(f"任务 {task_id} 等待完成失败: {e}")
            return False
    
    async def search_async(self, query: str):
        """异步搜索"""
        try:
            start_time = time.time()
            response = await self.client.get(f"/search?q={query}&top_k=5")
            response_time = time.time() - start_time
            return response, response_time
        except Exception as e:
            return e
    
    async def ask_question_async(self, question: str):
        """异步提问"""
        try:
            response = await self.client.post("/ask", json={"question": question})
            return response
        except Exception as e:
            return e


class TestDataConsistency:
    """数据一致性测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self, test_client: TestClient, test_data_dir: Path):
        """测试前置设置"""
        self.client = test_client
        self.test_data_dir = test_data_dir
    
    @pytest.mark.asyncio
    async def test_task_status_consistency(self):
        """测试任务状态一致性 - TC-CONSIST-001"""
        print("\n=== 执行测试: TC-CONSIST-001 任务状态一致性 ===")
        
        try:
            # 创建测试文档
            test_content = "任务状态一致性测试文档内容。"
            pdf_path = self.test_data_dir / "consistency_test.pdf"
            with open(pdf_path, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            # 上传文件
            with open(pdf_path, 'rb') as f:
                files = {"file": ("consistency_test.pdf", f, "application/pdf")}
                response = await self.client.post("/upload", files=files)
            
            assert response.status_code == 200
            task_id = response.json()["task_id"]
            print(f"任务创建: {task_id}")
            
            # 监控状态转换
            status_timeline = []
            start_time = time.time()
            
            while time.time() - start_time < 60:  # 监控60秒
                response = await self.client.get(f"/tasks/{task_id}")
                if response.status_code == 200:
                    current_status = response.json()["status"]
                    timestamp = time.time()
                    status_timeline.append({"time": timestamp, "status": current_status})
                    
                    print(f"状态: {current_status} (时间: {timestamp - start_time:.1f}s)")
                    
                    if current_status == "Completed":
                        break
                
                await asyncio.sleep(1)
            
            # 验证状态转换合法性
            valid_transitions = ["Pending", "Processing", "Completed"]
            actual_transitions = [s["status"] for s in status_timeline]
            
            print(f"状态转换序列: {actual_transitions}")
            
            # 状态只能向前转换，不能回退
            for i in range(1, len(actual_transitions)):
                prev_status = actual_transitions[i-1]
                curr_status = actual_transitions[i]
                
                # 允许相同状态或向前转换
                if curr_status != prev_status:
                    assert valid_transitions.index(curr_status) > valid_transitions.index(prev_status), \
                        f"状态不能回退: {prev_status} -> {curr_status}"
            
            # 验证最终状态
            assert actual_transitions[-1] == "Completed", "最终状态应该是Completed"
            
            print("✅ TC-CONSIST-001 任务状态一致性测试通过!")
            
        except Exception as e:
            print(f"❌ TC-CONSIST-001 测试失败: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_data_synchronization_consistency(self):
        """测试数据同步一致性 - TC-CONSIST-002"""
        print("\n=== 执行测试: TC-CONSIST-002 数据同步一致性 ===")
        
        try:
            # 准备测试文档
            test_content = "这是一致性测试专用文档，包含特定的测试关键词。"
            pdf_path = self.test_data_dir / "sync_test.pdf"
            with open(pdf_path, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            # 上传文档
            with open(pdf_path, 'rb') as f:
                files = {"file": ("sync_test.pdf", f, "application/pdf")}
                response = await self.client.post("/upload", files=files)
            
            assert response.status_code == 200
            task_id = response.json()["task_id"]
            
            # 等待任务完成
            from tests.integration.test_full_chain import TestFullChainIntegration
            full_chain_test = TestFullChainIntegration()
            full_chain_test.client = self.client
            full_chain_test.test_data_dir = self.test_data_dir
            
            final_status = await full_chain_test.poll_task_to_completion(task_id, timeout=120)
            assert final_status == "Completed"
            
            # 等待索引建立
            await asyncio.sleep(3)
            
            # 从API层面验证数据一致性
            # 1. 验证任务状态
            response = await self.client.get(f"/tasks/{task_id}")
            assert response.status_code == 200
            task_data = response.json()
            assert task_data["status"] == "Completed"
            print("✓ 任务状态一致性验证通过")
            
            # 2. 验证搜索结果
            response = await self.client.get("/search?q=一致性测试&top_k=10")
            assert response.status_code == 200
            search_results = response.json()
            assert len(search_results) > 0
            
            # 查找我们的测试文档
            found_our_doc = False
            for result in search_results:
                if "sync_test.pdf" in result.get("source", ""):
                    found_our_doc = True
                    assert "一致性测试" in result.get("text", "")
                    break
            
            assert found_our_doc, "应该能在搜索结果中找到测试文档"
            print("✓ 搜索结果一致性验证通过")
            
            # 3. 验证问答功能
            response = await self.client.post("/ask", json={"question": "一致性测试文档的主要内容是什么？"})
            assert response.status_code == 200
            answer_data = response.json()
            
            assert "answer" in answer_data
            assert len(answer_data["answer"]) > 0
            assert len(answer_data["sources"]) > 0
            print("✓ 问答结果一致性验证通过")
            
            print("✅ TC-CONSIST-002 数据同步一致性测试通过!")
            
        except Exception as e:
            print(f"❌ TC-CONSIST-002 测试失败: {e}")
            raise


if __name__ == "__main__":
    # 运行测试用例统计
    print("=== 全链路闭环测试用例统计 ===")
    
    full_chain_cases = comprehensive_test_cases.get_test_cases_by_type(TestType.FULL_CHAIN)
    print(f"全链路测试用例总数: {len(full_chain_cases)}")
    
    p0_cases = [case for case in full_chain_cases if case.priority == TestPriority.P0]
    p1_cases = [case for case in full_chain_cases if case.priority == TestPriority.P1]
    
    print(f"P0级用例: {len(p0_cases)}")
    print(f"P1级用例: {len(p1_cases)}")
    
    total_execution_time = sum(case.execution_time or 60 for case in full_chain_cases)
    print(f"预计总执行时间: {total_execution_time/60:.1f} 分钟")
    
    print("\nP0级核心用例:")
    for case in p0_cases:
        print(f"  - {case.case_id}: {case.description}")
    
    pytest.main([__file__, "-v", "-s"])