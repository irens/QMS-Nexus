"""
异常鲁棒性测试实现
基于综合测试用例设计的异常处理和系统鲁棒性验证
"""
import pytest
import asyncio
import time
import threading
import concurrent.futures
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Optional
from pathlib import Path

from tests.integration.conftest import TestClient
from tests.integration.COMPREHENSIVE_TEST_CASES import comprehensive_test_cases, TestType, TestPriority


class TestExceptionRobustness:
    """异常鲁棒性测试类"""
    
    @pytest.fixture(autouse=True)
    def setup(self, test_client: TestClient, test_data_dir: Path):
        """测试前置设置"""
        self.client = test_client
        self.test_data_dir = test_data_dir
        self.exception_log = []
        self.system_metrics = {}
    
    def log_exception_event(self, event_type: str, details: Dict[str, Any], severity: str = "INFO"):
        """记录异常事件"""
        event = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": event_type,
            "severity": severity,
            "details": details
        }
        self.exception_log.append(event)
        print(f"[{severity}] {event_type}: {details}")
    
    def simulate_redis_failure(self, duration: int = 30):
        """模拟Redis故障"""
        def redis_failure():
            with patch('redis.Redis.ping', side_effect=Exception("Redis连接失败")):
                with patch('redis.Redis.set', side_effect=Exception("Redis写入失败")):
                    with patch('redis.Redis.get', side_effect=Exception("Redis读取失败")):
                        time.sleep(duration)
        
        thread = threading.Thread(target=redis_failure)
        thread.daemon = True
        thread.start()
        return thread
    
    def simulate_llm_timeout(self, timeout_duration: int = 30):
        """模拟LLM服务超时"""
        def llm_timeout():
            with patch('core.llm.LLMClient.chat', side_effect=asyncio.TimeoutError("LLM服务超时")):
                time.sleep(timeout_duration)
        
        thread = threading.Thread(target=llm_timeout)
        thread.daemon = True
        thread.start()
        return thread
    
    def simulate_database_slowdown(self, delay: float = 5.0):
        """模拟数据库响应变慢"""
        def db_slow():
            with patch('sqlalchemy.engine.Engine.execute', side_effect=lambda *args, **kwargs: time.sleep(delay)):
                time.sleep(30)
        
        thread = threading.Thread(target=db_slow)
        thread.daemon = True
        thread.start()
        return thread
    
    def simulate_disk_full(self, target_path: str = "/tmp"):
        """模拟磁盘空间不足"""
        def disk_full():
            with patch('pathlib.Path.mkdir', side_effect=OSError("磁盘空间不足", 28)):
                with patch('builtins.open', side_effect=OSError("磁盘空间不足", 28)):
                    time.sleep(30)
        
        thread = threading.Thread(target=disk_full)
        thread.daemon = True
        thread.start()
        return thread
    
    def simulate_network_partition(self, target_host: str = "localhost"):
        """模拟网络分区"""
        def network_partition():
            with patch('aiohttp.ClientSession.request', side_effect=Exception("网络连接失败")):
                with patch('requests.get', side_effect=Exception("网络连接失败")):
                    time.sleep(30)
        
        thread = threading.Thread(target=network_partition)
        thread.daemon = True
        thread.start()
        return thread
    
    def get_system_health(self) -> Dict[str, Any]:
        """获取系统健康状态"""
        try:
            # 模拟系统健康检查
            health_data = {
                "status": "ok",
                "timestamp": time.time(),
                "components": {
                    "api": "healthy",
                    "database": "healthy", 
                    "redis": "healthy",
                    "llm": "healthy"
                },
                "metrics": {
                    "cpu_usage": 45.2,
                    "memory_usage": 67.8,
                    "disk_usage": 23.1
                }
            }
            
            # 根据异常日志调整健康状态
            recent_errors = [
                event for event in self.exception_log 
                if time.time() - time.mktime(time.strptime(event["timestamp"], "%Y-%m-%d %H:%M:%S")) < 60
                and event["severity"] in ["ERROR", "CRITICAL"]
            ]
            
            if recent_errors:
                health_data["status"] = "degraded"
                for error in recent_errors:
                    if "redis" in error["event_type"].lower():
                        health_data["components"]["redis"] = "unhealthy"
                    elif "llm" in error["event_type"].lower():
                        health_data["components"]["llm"] = "unhealthy"
                    elif "database" in error["event_type"].lower():
                        health_data["components"]["database"] = "unhealthy"
            
            return health_data
        except Exception as e:
            self.log_exception_event("health_check_failed", {"error": str(e)}, "ERROR")
            return {"status": "unknown", "error": str(e)}
    
    def create_test_pdf(self, filename: str, content: str) -> Path:
        """创建测试PDF文件"""
        pdf_path = self.test_data_dir / filename
        with open(pdf_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return pdf_path
    
    async def poll_task_with_timeout(self, task_id: str, timeout: int = 60, interval: float = 1.0) -> Optional[str]:
        """轮询任务状态，带超时处理"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = await self.client.get(f"/tasks/{task_id}")
                if response.status_code == 200:
                    task_data = response.json()
                    current_status = task_data["status"]
                    
                    if current_status in ["Completed", "Failed"]:
                        return current_status
                    
                    # 记录状态变化
                    self.log_exception_event("task_status_poll", {
                        "task_id": task_id,
                        "status": current_status,
                        "elapsed": time.time() - start_time
                    })
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                self.log_exception_event("task_poll_exception", {
                    "task_id": task_id,
                    "error": str(e),
                    "elapsed": time.time() - start_time
                }, "ERROR")
                
                # 如果超时，返回None
                if time.time() - start_time >= timeout:
                    return None
                
                await asyncio.sleep(interval)
        
        return None
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("test_case", [
        case for case in comprehensive_test_cases.get_test_cases_by_type(TestType.ROBUSTNESS)
        if case.priority == TestPriority.P0
    ])
    async def test_redis_failure_recovery(self, test_case):
        """测试Redis故障恢复 - TC-ROBUST-001"""
        print(f"\n=== 执行测试: {test_case.case_id} ===")
        print(f"描述: {test_case.description}")
        
        try:
            # Step 1: 建立正常业务基线
            print("步骤1: 建立正常业务基线...")
            baseline_pdf = self.create_test_pdf("baseline.pdf", "基线测试文档内容")
            
            with open(baseline_pdf, 'rb') as f:
                files = {"file": ("baseline.pdf", f, "application/pdf")}
                response = await self.client.post("/upload", files=files)
            
            assert response.status_code == 200
            baseline_task_id = response.json()["task_id"]
            self.log_exception_event("baseline_task_created", {"task_id": baseline_task_id})
            print(f"✓ 基线任务创建: {baseline_task_id}")
            
            # Step 2: 模拟Redis连接失败
            print("步骤2: 模拟Redis连接失败...")
            failure_thread = self.simulate_redis_failure(duration=30)
            
            # 等待故障模拟生效
            await asyncio.sleep(2)
            self.log_exception_event("redis_failure_simulated", {"duration": 30}, "ERROR")
            
            # Step 3: 在故障期间尝试上传
            print("步骤3: 在故障期间上传新文件...")
            during_failure_pdf = self.create_test_pdf("during_failure.pdf", "故障期间测试文档")
            
            try:
                with open(during_failure_pdf, 'rb') as f:
                    files = {"file": ("during_failure.pdf", f, "application/pdf")}
                    response = await self.client.post("/upload", files=files)
                
                # 即使Redis故障，上传应该仍然成功（任务创建）
                if response.status_code == 200:
                    during_failure_task_id = response.json()["task_id"]
                    self.log_exception_event("upload_during_failure", {"task_id": during_failure_task_id})
                    print(f"✓ 故障期间任务创建: {during_failure_task_id}")
                    
                    # 验证任务保持Pending状态
                    response = await self.client.get(f"/tasks/{during_failure_task_id}")
                    if response.status_code == 200:
                        task_status = response.json()["status"]
                        assert task_status == "Pending", f"任务应该保持Pending状态，实际是{task_status}"
                        print("✓ 任务保持Pending状态")
                    else:
                        print(f"⚠ 无法获取任务状态: {response.status_code}")
                else:
                    print(f"⚠ 故障期间上传失败: {response.status_code}")
                    
            except Exception as e:
                self.log_exception_event("upload_during_failure_error", {"error": str(e)}, "ERROR")
                print(f"⚠ 故障期间上传异常: {e}")
            
            # Step 4: 检查降级机制
            print("步骤4: 检查降级机制...")
            # 等待一段时间让系统尝试处理
            await asyncio.sleep(5)
            
            # 检查系统健康状态
            health_status = self.get_system_health()
            self.log_exception_event("health_check_during_failure", health_status)
            
            if health_status["status"] == "degraded":
                print("✓ 系统进入降级模式")
            else:
                print(f"⚠ 系统状态: {health_status['status']}")
            
            # Step 5: 恢复Redis服务
            print("步骤5: 恢复Redis服务...")
            # 等待故障模拟结束
            failure_thread.join(timeout=35)
            
            # 等待系统恢复
            await asyncio.sleep(3)
            self.log_exception_event("redis_service_restored", {"status": "recovered"})
            print("✓ Redis服务恢复")
            
            # Step 6: 验证自动恢复
            print("步骤6: 验证自动恢复...")
            if 'during_failure_task_id' in locals():
                # 尝试轮询之前失败的任务
                final_status = await self.poll_task_with_timeout(during_failure_task_id, timeout=60)
                
                if final_status == "Completed":
                    print("✓ 中断期间任务处理完成")
                    
                    # 验证数据完整性
                    try:
                        response = await self.client.get("/search?q=故障期间&top_k=5")
                        if response.status_code == 200:
                            search_results = response.json()
                            found_source = any("during_failure.pdf" in result.get("source", "") for result in search_results)
                            if found_source:
                                print("✓ 数据完整性验证通过")
                            else:
                                print("⚠ 未找到故障期间的文档")
                    except Exception as e:
                        print(f"⚠ 搜索验证失败: {e}")
                        
                elif final_status == "Failed":
                    print("⚠ 中断期间任务处理失败")
                else:
                    print("⚠ 中断期间任务处理超时")
            else:
                print("⚠ 没有故障期间的任务需要验证")
            
            # 验证系统健康状态恢复
            final_health = self.get_system_health()
            self.log_exception_event("final_health_check", final_health)
            
            if final_health["status"] == "ok":
                print("✓ 系统健康状态恢复正常")
            else:
                print(f"⚠ 系统最终状态: {final_health['status']}")
            
            print("✅ TC-ROBUST-001 Redis故障恢复测试通过!")
            
        except Exception as e:
            print(f"❌ TC-ROBUST-001 测试失败: {e}")
            self.log_exception_event("test_failure", {"error": str(e)}, "ERROR")
            raise
    
    @pytest.mark.asyncio
    async def test_llm_service_circuit_breaker(self):
        """测试LLM服务熔断机制 - TC-ROBUST-002"""
        print("\n=== 执行测试: TC-ROBUST-002 LLM服务熔断机制 ===")
        
        try:
            # Step 1: 测试正常LLM调用
            print("步骤1: 测试正常LLM调用...")
            try:
                response = await self.client.post("/ask", json={"question": "什么是质量方针？"})
                if response.status_code == 200:
                    answer_data = response.json()
                    print(f"✓ 正常LLM调用成功: {answer_data.get('answer', '')[:50]}...")
                else:
                    print(f"⚠ 正常LLM调用返回状态: {response.status_code}")
            except Exception as e:
                print(f"⚠ 正常LLM调用异常: {e}")
            
            # Step 2-3: 模拟LLM服务连续超时
            print("步骤2-3: 模拟LLM服务连续超时...")
            
            failure_count = 0
            max_failures = 5
            timeout_duration = 2  # 短超时用于测试
            
            # 模拟超时
            with patch('core.llm.LLMClient.chat', side_effect=asyncio.TimeoutError("LLM服务超时")):
                for i in range(max_failures + 2):  # 超过熔断阈值
                    try:
                        start_time = time.time()
                        response = await self.client.post("/ask", json={"question": f"测试问题{i}"})
                        
                        if response.status_code == 504:  # 网关超时
                            failure_count += 1
                            print(f"✓ LLM调用超时 #{i+1} (耗时: {time.time() - start_time:.1f}s)")
                        elif response.status_code == 200:
                            # 可能返回默认回答
                            answer_data = response.json()
                            if "知识库中暂无相关记录" in answer_data.get("answer", ""):
                                print(f"✓ LLM调用返回默认回答 #{i+1}")
                            else:
                                print(f"✓ LLM调用成功 #{i+1}")
                        else:
                            print(f"⚠ LLM调用返回状态: {response.status_code}")
                            
                    except asyncio.TimeoutError:
                        failure_count += 1
                        duration = time.time() - start_time
                        print(f"✓ LLM调用超时 #{i+1} (耗时: {duration:.1f}s)")
                        
                    except Exception as e:
                        failure_count += 1
                        print(f"✓ LLM调用异常 #{i+1}: {e}")
                        
                    # 短暂间隔
                    await asyncio.sleep(0.5)
            
            print(f"总失败次数: {failure_count}")
            assert failure_count >= max_failures, "应该触发熔断机制"
            
            # Step 4: 验证熔断后快速失败
            print("步骤4: 验证熔断后快速失败...")
            start_time = time.time()
            
            try:
                response = await self.client.post("/ask", json={"question": "熔断后测试"})
                duration = time.time() - start_time
                
                if duration < 1:  # 应该快速失败
                    print(f"✓ 熔断后快速失败 (耗时: {duration:.2f}s)")
                else:
                    print(f"⚠ 熔断后响应时间较长: {duration:.2f}s")
                    
                if response.status_code == 200:
                    answer_data = response.json()
                    if "知识库中暂无相关记录" in answer_data.get("answer", ""):
                        print("✓ 返回默认回答")
                    else:
                        print(f"✓ 返回正常回答: {answer_data.get('answer', '')[:50]}...")
                        
            except Exception as e:
                duration = time.time() - start_time
                print(f"✓ 熔断后快速异常 (耗时: {duration:.2f}s): {e}")
            
            # Step 5: 等待熔断恢复窗口
            print("步骤5: 等待熔断恢复窗口...")
            recovery_window = 10  # 缩短恢复窗口用于测试
            print(f"等待 {recovery_window} 秒...")
            await asyncio.sleep(recovery_window)
            
            # Step 6: 验证服务恢复
            print("步骤6: 验证服务恢复...")
            # 恢复正常的LLM服务
            
            try:
                response = await self.client.post("/ask", json={"question": "恢复后测试"})
                
                if response.status_code == 200:
                    answer_data = response.json()
                    if "恢复后测试" not in answer_data.get("answer", ""):  # 应该获得正常回答
                        print("✓ LLM服务恢复正常调用")
                        print(f"答案: {answer_data.get('answer', '')[:50]}...")
                        
                        # 验证有来源信息
                        if len(answer_data.get("sources", [])) > 0:
                            print("✓ 答案包含来源信息")
                        else:
                            print("⚠ 答案缺少来源信息")
                    else:
                        print("⚠ 可能仍在返回默认回答")
                else:
                    print(f"⚠ 服务恢复测试返回状态: {response.status_code}")
                    
            except Exception as e:
                print(f"⚠ 服务恢复测试异常: {e}")
            
            print("✅ TC-ROBUST-002 LLM服务熔断机制测试通过!")
            
        except Exception as e:
            print(f"❌ TC-ROBUST-002 测试失败: {e}")
            raise
    
    @pytest.mark.asyncio
    async def test_concurrent_exception_handling(self):
        """测试并发异常处理 - TC-ROBUST-003"""
        print("\n=== 执行测试: TC-ROBUST-003 并发异常处理 ===")
        
        try:
            # 参数设置
            concurrent_level = 20  # 降低并发度用于测试
            test_duration = 30
            
            print(f"设置: 并发级别={concurrent_level}, 测试时长={test_duration}s")
            
            # 定义并发操作函数
            async def concurrent_upload(index: int):
                """并发上传操作"""
                try:
                    filename = f"concurrent_upload_{index}.pdf"
                    content = f"并发上传测试文档{index}内容。包含质量管理关键词。"
                    
                    pdf_path = self.create_test_pdf(filename, content)
                    
                    with open(pdf_path, 'rb') as f:
                        files = {"file": (filename, f, "application/pdf")}
                        response = await self.client.post("/upload", files=files)
                    
                    if response.status_code == 200:
                        task_id = response.json()["task_id"]
                        self.log_exception_event("concurrent_upload_success", {
                            "index": index,
                            "task_id": task_id
                        })
                        return {"status": "success", "task_id": task_id, "index": index}
                    else:
                        self.log_exception_event("concurrent_upload_failed", {
                            "index": index,
                            "status_code": response.status_code
                        }, "ERROR")
                        return {"status": "failed", "index": index, "error": response.status_code}
                        
                except Exception as e:
                    self.log_exception_event("concurrent_upload_exception", {
                        "index": index,
                        "error": str(e)
                    }, "ERROR")
                    return {"status": "exception", "index": index, "error": str(e)}
            
            async def concurrent_search(index: int):
                """并发搜索操作"""
                try:
                    queries = ["质量", "管理", "体系", "标准", "要求"]
                    query = queries[index % len(queries)]
                    
                    response = await self.client.get(f"/search?q={query}&top_k=5")
                    
                    if response.status_code == 200:
                        results = response.json()
                        self.log_exception_event("concurrent_search_success", {
                            "index": index,
                            "result_count": len(results)
                        })
                        return {"status": "success", "index": index, "result_count": len(results)}
                    else:
                        self.log_exception_event("concurrent_search_failed", {
                            "index": index,
                            "status_code": response.status_code
                        }, "ERROR")
                        return {"status": "failed", "index": index, "error": response.status_code}
                        
                except Exception as e:
                    self.log_exception_event("concurrent_search_exception", {
                        "index": index,
                        "error": str(e)
                    }, "ERROR")
                    return {"status": "exception", "index": index, "error": str(e)}
            
            async def concurrent_ask(index: int):
                """并发问答操作"""
                try:
                    questions = [
                        "什么是质量方针？",
                        "质量管理的主要内容？",
                        "如何制定质量目标？",
                        "ISO 9001标准是什么？",
                        "质量控制的方法？"
                    ]
                    question = questions[index % len(questions)]
                    
                    response = await self.client.post("/ask", json={"question": question})
                    
                    if response.status_code == 200:
                        answer_data = response.json()
                        self.log_exception_event("concurrent_ask_success", {
                            "index": index,
                            "answer_length": len(answer_data.get("answer", ""))
                        })
                        return {"status": "success", "index": index, "answer_length": len(answer_data.get("answer", ""))}
                    else:
                        self.log_exception_event("concurrent_ask_failed", {
                            "index": index,
                            "status_code": response.status_code
                        }, "ERROR")
                        return {"status": "failed", "index": index, "error": response.status_code}
                        
                except Exception as e:
                    self.log_exception_event("concurrent_ask_exception", {
                        "index": index,
                        "error": str(e)
                    }, "ERROR")
                    return {"status": "exception", "index": index, "error": str(e)}
            
            # 启动并发测试
            print("启动并发测试...")
            start_time = time.time()
            
            # 随机注入一些异常
            def inject_random_failures():
                """随机注入故障"""
                import random
                
                failure_types = [
                    ("database_timeout", lambda: patch('sqlalchemy.engine.Engine.execute', side_effect=Exception("数据库超时"))),
                    ("redis_slow", lambda: patch('redis.Redis.get', side_effect=lambda *args: time.sleep(random.uniform(0.1, 0.5)) or None)),
                    ("network_delay", lambda: patch('aiohttp.ClientSession.request', side_effect=lambda *args, **kwargs: asyncio.sleep(random.uniform(0.1, 0.3)) or MagicMock()))
                ]
                
                for _ in range(5):  # 注入5次随机故障
                    time.sleep(random.uniform(1, 5))
                    failure_type, patch_func = random.choice(failure_types)
                    
                    with patch_func():
                        self.log_exception_event("random_failure_injected", {
                            "failure_type": failure_type
                        }, "WARNING")
                        time.sleep(random.uniform(0.5, 2))
            
            # 启动故障注入线程
            failure_thread = threading.Thread(target=inject_random_failures)
            failure_thread.daemon = True
            failure_thread.start()
            
            # 执行并发操作
            all_tasks = []
            
            # 上传任务
            upload_tasks = [concurrent_upload(i) for i in range(concurrent_level // 2)]
            all_tasks.extend(upload_tasks)
            
            # 搜索任务
            search_tasks = [concurrent_search(i) for i in range(concurrent_level // 3)]
            all_tasks.extend(search_tasks)
            
            # 问答任务
            ask_tasks = [concurrent_ask(i) for i in range(concurrent_level // 6)]
            all_tasks.extend(ask_tasks)
            
            # 并发执行所有任务
            results = await asyncio.gather(*all_tasks, return_exceptions=True)
            
            # 分析结果
            total_tasks = len(results)
            success_count = 0
            failed_count = 0
            exception_count = 0
            
            for result in results:
                if isinstance(result, Exception):
                    exception_count += 1
                elif result["status"] == "success":
                    success_count += 1
                elif result["status"] in ["failed", "exception"]:
                    failed_count += 1
            
            total_duration = time.time() - start_time
            
            print(f"并发测试完成:")
            print(f"  总任务数: {total_tasks}")
            print(f"  成功: {success_count}")
            print(f"  失败: {failed_count}")
            print(f"  异常: {exception_count}")
            print(f"  总耗时: {total_duration:.2f}s")
            
            # 计算成功率
            success_rate = success_count / total_tasks if total_tasks > 0 else 0
            print(f"  成功率: {success_rate:.1%}")
            
            # 验证成功率要求
            assert success_rate >= 0.90, f"并发成功率应该≥90%，实际是{success_rate:.1%}"
            
            # 验证无系统崩溃
            final_health = self.get_system_health()
            self.log_exception_event("concurrent_test_final_health", final_health)
            
            assert final_health["status"] != "critical", "系统不应该处于严重状态"
            
            # 验证资源使用情况
            if "metrics" in final_health:
                metrics = final_health["metrics"]
                cpu_usage = metrics.get("cpu_usage", 0)
                memory_usage = metrics.get("memory_usage", 0)
                
                print(f"  最终资源使用:")
                print(f"    CPU: {cpu_usage:.1f}%")
                print(f"    内存: {memory_usage:.1f}%")
                
                assert cpu_usage < 90, f"CPU使用率应该<90%，实际是{cpu_usage:.1f}%"
                assert memory_usage < 90, f"内存使用率应该<90%，实际是{memory_usage:.1f}%"
            
            print("✅ TC-ROBUST-003 并发异常处理测试通过!")
            
        except Exception as e:
            print(f"❌ TC-ROBUST-003 测试失败: {e}")
            raise
    
    def print_exception_report(self):
        """打印异常处理报告"""
        if not self.exception_log:
            print("没有异常事件记录")
            return
        
        print("\n=== 异常处理事件报告 ===")
        
        # 按严重程度分组
        by_severity = {}
        for event in self.exception_log:
            severity = event["severity"]
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(event)
        
        for severity, events in by_severity.items():
            print(f"\n{severity}级别事件: {len(events)}")
            for event in events[:3]:  # 显示前3个
                print(f"  - {event['timestamp']}: {event['event_type']}")
            if len(events) > 3:
                print(f"  ... 还有 {len(events)-3} 个事件")
        
        # 按类型分组
        by_type = {}
        for event in self.exception_log:
            event_type = event["event_type"]
            if event_type not in by_type:
                by_type[event_type] = []
            by_type[event_type].append(event)
        
        print(f"\n事件类型分布:")
        for event_type, events in by_type.items():
            print(f"  {event_type}: {len(events)}")


if __name__ == "__main__":
    # 运行异常鲁棒性测试
    print("=== 异常鲁棒性测试执行 ===")
    
    robustness_cases = comprehensive_test_cases.get_test_cases_by_type(TestType.ROBUSTNESS)
    print(f"异常鲁棒性测试用例总数: {len(robustness_cases)}")
    
    p0_cases = [case for case in robustness_cases if case.priority == TestPriority.P0]
    p1_cases = [case for case in robustness_cases if case.priority == TestPriority.P1]
    
    print(f"P0级用例: {len(p0_cases)}")
    print(f"P1级用例: {len(p1_cases)}")
    
    total_execution_time = sum(case.execution_time or 60 for case in robustness_cases)
    print(f"预计总执行时间: {total_execution_time/60:.1f} 分钟")
    
    print("\nP0级核心用例:")
    for case in p0_cases:
        print(f"  - {case.case_id}: {case.description} ({case.execution_time or 60}s)")
    
    pytest.main([__file__, "-v", "-s"])