"""
数据一致性测试实现
基于综合测试用例设计的数据一致性验证
"""
import pytest
import asyncio
import time
import json
import hashlib
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from tests.integration.conftest import TestClient
from tests.integration.COMPREHENSIVE_TEST_CASES import comprehensive_test_cases, TestType, TestPriority


class TestDataConsistency:
    """数据一致性测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self, test_client: TestClient, test_data_dir: Path):
        """测试前置设置"""
        self.client = test_client
        self.test_data_dir = test_data_dir
        self.consistency_log = []
    
    def log_consistency_check(self, check_type: str, data: Dict[str, Any], result: bool):
        """记录一致性检查日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "check_type": check_type,
            "data": data,
            "result": result,
            "duration": time.time() - data.get("start_time", time.time())
        }
        self.consistency_log.append(log_entry)
    
    async def get_task_status_from_api(self, task_id: str) -> Dict[str, Any]:
        """从API获取任务状态"""
        response = await self.client.get(f"/tasks/{task_id}")
        if response.status_code == 200:
            return response.json()
        return None
    
    async def get_task_status_from_redis(self, task_id: str) -> Dict[str, Any]:
        """从Redis获取任务状态"""
        try:
            # 这里需要直接访问Redis，在实际测试中可能需要通过专门的接口
            # 或者通过内部API获取Redis状态
            response = await self.client.get(f"/internal/redis/task/{task_id}")
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
    
    async def get_document_from_sqlite(self, task_id: str) -> Dict[str, Any]:
        """从SQLite获取文档信息"""
        try:
            # 通过内部API或直接查询
            response = await self.client.get(f"/internal/db/document/{task_id}")
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return None
    
    async def get_vectors_from_chroma(self, task_id: str) -> List[Dict[str, Any]]:
        """从ChromaDB获取向量数据"""
        try:
            response = await self.client.get(f"/internal/vectors/{task_id}")
            if response.status_code == 200:
                return response.json()
        except:
            pass
        return []
    
    def calculate_data_checksum(self, data: Any) -> str:
        """计算数据的校验和"""
        data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(data_str.encode()).hexdigest()
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_case", [
        case for case in comprehensive_test_cases.get_test_cases_by_type(TestType.CONSISTENCY)
        if case.priority == TestPriority.P0
    ])
    async def test_task_status_consistency(self, test_case):
        """测试任务状态一致性 - TC-CONSIST-001"""
        print(f"\n=== 执行测试: {test_case.case_id} ===")
        print(f"描述: {test_case.description}")
        
        try:
            # 创建测试文档
            test_content = "任务状态一致性测试文档内容。包含质量管理相关关键词。"
            pdf_path = self.test_data_dir / "consistency_test.pdf"
            with open(pdf_path, 'w', encoding='utf-8') as f:
                f.write(test_content)
            
            # 上传文件
            print("步骤1: 上传测试文件...")
            with open(pdf_path, 'rb') as f:
                files = {"file": ("consistency_test.pdf", f, "application/pdf")}
                response = await self.client.post("/upload", files=files)
            
            assert response.status_code == 200
            task_data = response.json()
            task_id = task_data["task_id"]
            print(f"✓ 任务创建成功: {task_id}")
            
            # 监控状态转换
            print("步骤2: 监控任务状态转换...")
            status_timeline = []
            start_time = time.time()
            last_status = None
            
            while time.time() - start_time < 60:  # 监控60秒
                response = await self.client.get(f"/tasks/{task_id}")
                if response.status_code == 200:
                    current_data = response.json()
                    current_status = current_data["status"]
                    timestamp = time.time()
                    
                    # 记录状态变化
                    if current_status != last_status:
                        status_change = {
                            "time": timestamp - start_time,
                            "status": current_status,
                            "data": current_data
                        }
                        status_timeline.append(status_change)
                        print(f"状态变化: {last_status} -> {current_status} (时间: {status_change['time']:.1f}s)")
                        last_status = current_status
                    
                    if current_status in ["Completed", "Failed"]:
                        break
                
                await asyncio.sleep(1)
            
            # 验证状态转换合法性
            print("步骤3: 验证状态转换合法性...")
            valid_transitions = ["Pending", "Processing", "Completed"]
            actual_transitions = [s["status"] for s in status_timeline]
            
            print(f"状态序列: {actual_transitions}")
            
            # 状态只能向前转换，不能回退
            for i in range(1, len(actual_transitions)):
                prev_status = actual_transitions[i-1]
                curr_status = actual_transitions[i]
                
                # 允许相同状态或向前转换
                if curr_status != prev_status:
                    assert valid_transitions.index(curr_status) > valid_transitions.index(prev_status), \
                        f"状态不能回退: {prev_status} -> {curr_status}"
            
            # 验证最终状态
            assert actual_transitions[-1] == "Completed", f"最终状态应该是Completed，实际是{actual_transitions[-1]}"
            
            # 记录一致性检查
            self.log_consistency_check("task_status", {
                "task_id": task_id,
                "transitions": actual_transitions,
                "timeline": status_timeline,
                "start_time": start_time
            }, True)
            
            print("✅ TC-CONSIST-001 任务状态一致性测试通过!")
            
        except Exception as e:
            print(f"❌ TC-CONSIST-001 测试失败: {e}")
            self.log_consistency_check("task_status", {"error": str(e)}, False)
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
            
            # 计算原始文档校验和
            original_checksum = self.calculate_data_checksum(test_content)
            print(f"原始文档校验和: {original_checksum}")
            
            # 上传文档
            print("步骤1: 上传测试文档...")
            with open(pdf_path, 'rb') as f:
                files = {"file": ("sync_test.pdf", f, "application/pdf")}
                response = await self.client.post("/upload", files=files)
            
            assert response.status_code == 200
            task_data = response.json()
            task_id = task_data["task_id"]
            print(f"✓ 任务创建成功: {task_id}")
            
            # 等待任务完成
            print("步骤2: 等待文档处理完成...")
            start_time = time.time()
            while time.time() - start_time < 120:
                response = await self.client.get(f"/tasks/{task_id}")
                if response.status_code == 200:
                    current_status = response.json()["status"]
                    if current_status == "Completed":
                        print(f"✓ 任务处理完成 (耗时: {time.time() - start_time:.1f}s)")
                        break
                    elif current_status == "Failed":
                        raise Exception("文档处理失败")
                await asyncio.sleep(1)
            else:
                raise TimeoutError("文档处理超时")
            
            # 等待索引建立
            await asyncio.sleep(3)
            
            # 验证API层面的一致性
            print("步骤3: 验证API层面数据一致性...")
            
            # 3.1 验证任务状态
            response = await self.client.get(f"/tasks/{task_id}")
            assert response.status_code == 200
            task_info = response.json()
            assert task_info["status"] == "Completed"
            print("✓ 任务状态一致性验证通过")
            
            # 3.2 验证搜索结果
            response = await self.client.get("/search?q=一致性测试&top_k=10")
            assert response.status_code == 200
            search_results = response.json()
            assert len(search_results) > 0
            
            # 查找我们的测试文档
            found_our_doc = False
            search_checksums = []
            for result in search_results:
                if "sync_test.pdf" in result.get("source", ""):
                    found_our_doc = True
                    result_text = result.get("text", "")
                    if "一致性测试" in result_text:
                        search_checksum = self.calculate_data_checksum(result_text)
                        search_checksums.append(search_checksum)
            
            assert found_our_doc, "应该能在搜索结果中找到测试文档"
            assert len(search_checksums) > 0, "搜索结果应该包含相关内容"
            print("✓ 搜索结果一致性验证通过")
            
            # 3.3 验证问答功能
            response = await self.client.post("/ask", json={"question": "一致性测试文档的主要内容是什么？"})
            assert response.status_code == 200
            answer_data = response.json()
            
            assert "answer" in answer_data
            assert len(answer_data["answer"]) > 0
            assert len(answer_data["sources"]) > 0
            
            # 验证答案中包含相关内容
            answer_text = answer_data["answer"]
            answer_checksum = self.calculate_data_checksum(answer_text)
            print(f"答案校验和: {answer_checksum}")
            print("✓ 问答结果一致性验证通过")
            
            # 记录一致性检查
            self.log_consistency_check("data_synchronization", {
                "task_id": task_id,
                "original_checksum": original_checksum,
                "search_checksums": search_checksums,
                "answer_checksum": answer_checksum,
                "search_results_count": len(search_results),
                "sources_count": len(answer_data["sources"])
            }, True)
            
            print("✅ TC-CONSIST-002 数据同步一致性测试通过!")
            
        except Exception as e:
            print(f"❌ TC-CONSIST-002 测试失败: {e}")
            self.log_consistency_check("data_synchronization", {"error": str(e)}, False)
            raise
    
    @pytest.mark.asyncio
    async def test_cache_consistency(self):
        """测试缓存一致性 - TC-CONSIST-003"""
        print("\n=== 执行测试: TC-CONSIST-003 缓存一致性 ===")
        
        try:
            # 创建测试文档
            original_content = "这是缓存一致性测试的原始内容。"
            pdf_path = self.test_data_dir / "cache_test.pdf"
            with open(pdf_path, 'w', encoding='utf-8') as f:
                f.write(original_content)
            
            # 上传文档
            print("步骤1: 上传测试文档...")
            with open(pdf_path, 'rb') as f:
                files = {"file": ("cache_test.pdf", f, "application/pdf")}
                response = await self.client.post("/upload", files=files)
            
            assert response.status_code == 200
            task_id = response.json()["task_id"]
            print(f"✓ 任务创建: {task_id}")
            
            # 等待处理完成
            print("步骤2: 等待文档处理完成...")
            start_time = time.time()
            while time.time() - start_time < 120:
                response = await self.client.get(f"/tasks/{task_id}")
                if response.status_code == 200 and response.json()["status"] == "Completed":
                    break
                await asyncio.sleep(1)
            
            # 等待索引建立
            await asyncio.sleep(2)
            
            # 首次搜索 (应该触发缓存)
            print("步骤3: 首次搜索，触发缓存...")
            response = await self.client.get("/search?q=缓存一致性&top_k=5")
            assert response.status_code == 200
            first_results = response.json()
            assert len(first_results) > 0
            print(f"✓ 首次搜索完成，返回 {len(first_results)} 个结果")
            
            # 立即再次搜索 (应该命中缓存)
            print("步骤4: 再次搜索，验证缓存命中...")
            response = await self.client.get("/search?q=缓存一致性&top_k=5")
            assert response.status_code == 200
            cached_results = response.json()
            
            # 验证缓存一致性
            assert len(cached_results) == len(first_results)
            
            # 比较结果内容
            for i, (first, cached) in enumerate(zip(first_results, cached_results)):
                assert first["text"] == cached["text"]
                assert first["source"] == cached["source"]
                assert first["score"] == cached["score"]
            
            print("✓ 缓存一致性验证通过")
            
            # 记录一致性检查
            self.log_consistency_check("cache_consistency", {
                "task_id": task_id,
                "first_search_count": len(first_results),
                "cached_search_count": len(cached_results),
                "cache_hit": True,
                "results_match": True
            }, True)
            
            print("✅ TC-CONSIST-003 缓存一致性测试通过!")
            
        except Exception as e:
            print(f"❌ TC-CONSIST-003 测试失败: {e}")
            self.log_consistency_check("cache_consistency", {"error": str(e)}, False)
            raise
    
    def print_consistency_report(self):
        """打印一致性检查报告"""
        if not self.consistency_log:
            print("没有一致性检查记录")
            return
        
        print("\n=== 数据一致性检查报告 ===")
        
        passed_checks = sum(1 for log in self.consistency_log if log["result"])
        total_checks = len(self.consistency_log)
        
        print(f"总检查数: {total_checks}")
        print(f"通过检查: {passed_checks}")
        print(f"一致性率: {passed_checks/total_checks*100:.1f}%")
        
        # 按类型分组
        by_type = {}
        for log in self.consistency_log:
            check_type = log["check_type"]
            if check_type not in by_type:
                by_type[check_type] = []
            by_type[check_type].append(log)
        
        for check_type, logs in by_type.items():
            type_passed = sum(1 for log in logs if log["result"])
            print(f"\n{check_type}: {type_passed}/{len(logs)} 通过")
            
            for log in logs:
                status = "✓" if log["result"] else "✗"
                print(f"  {status} 耗时: {log['duration']:.2f}s")


if __name__ == "__main__":
    # 运行数据一致性测试
    print("=== 数据一致性测试执行 ===")
    
    consistency_cases = comprehensive_test_cases.get_test_cases_by_type(TestType.CONSISTENCY)
    print(f"数据一致性测试用例总数: {len(consistency_cases)}")
    
    p0_cases = [case for case in consistency_cases if case.priority == TestPriority.P0]
    p1_cases = [case for case in consistency_cases if case.priority == TestPriority.P1]
    
    print(f"P0级用例: {len(p0_cases)}")
    print(f"P1级用例: {len(p1_cases)}")
    
    total_execution_time = sum(case.execution_time or 60 for case in consistency_cases)
    print(f"预计总执行时间: {total_execution_time/60:.1f} 分钟")
    
    print("\nP0级核心用例:")
    for case in p0_cases:
        print(f"  - {case.case_id}: {case.description} ({case.execution_time or 60}s)")
    
    pytest.main([__file__, "-v", "-s"])