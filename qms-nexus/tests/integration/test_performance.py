"""
性能测试用例实现
基于测试设计文档的性能测试代码
"""
import pytest
import time
import asyncio
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any
from fastapi.testclient import TestClient
import statistics


class TestPerformance:
    """性能测试类"""
    
    def test_concurrent_upload_performance(self, test_client: TestClient):
        """PF-UP-01: 并发上传性能测试"""
        
        import tempfile
        
        # 创建多个测试文件
        test_files = []
        for i in range(5):  # 5个并发上传
            content = f"%PDF-1.4\n测试内容{i}\n" + "测试文本" * 100
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
                tmp.write(content.encode())
                test_files.append(Path(tmp.name))
        
        try:
            start_time = time.time()
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
                        status_code, result = future.result(timeout=30)
                        results.append((status_code, result))
                    except Exception as e:
                        results.append((500, {"error": str(e)}))
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # 验证结果
            success_count = sum(1 for status, _ in results if status == 200)
            assert success_count == 5, f"期望5个成功，实际{success_count}个"
            
            # 性能要求：5个并发上传应在10秒内完成
            assert total_time < 10, f"并发上传耗时{total_time:.2f}秒，超过10秒限制"
            
            # 计算平均响应时间
            avg_time = total_time / 5
            
            print(f"✅ PF-UP-01通过: 5个并发上传，总耗时{total_time:.2f}秒，平均{avg_time:.2f}秒/个")
            
        finally:
            # 清理临时文件
            for file_path in test_files:
                file_path.unlink(missing_ok=True)
    
    def test_concurrent_search_performance(self, test_client: TestClient):
        """PF-SR-01: 并发搜索性能测试"""
        
        queries = [
            "质量方针",
            "质量管理",
            "质量目标",
            "质量要求",
            "质量评估",
            "质量控制",
            "质量保证",
            "质量改进",
            "质量审核",
            "质量标准"
        ]
        
        start_time = time.time()
        results = []
        
        def search_query(query: str):
            start_query = time.time()
            response = test_client.get(f"/search?q={query}&top_k=5")
            end_query = time.time()
            return {
                "query": query,
                "status_code": response.status_code,
                "response_time": end_query - start_query,
                "result_count": len(response.json()) if response.status_code == 200 else 0
            }
        
        # 并发搜索（10个查询）
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(search_query, query) for query in queries]
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    result = future.result(timeout=10)
                    results.append(result)
                except Exception as e:
                    results.append({"query": "error", "status_code": 500, "response_time": 10, "result_count": 0})
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 验证结果
        success_count = sum(1 for r in results if r["status_code"] == 200)
        assert success_count >= 8, f"期望至少8个成功，实际{success_count}个"
        
        # 性能要求：10个并发查询应在5秒内完成
        assert total_time < 5, f"并发搜索耗时{total_time:.2f}秒，超过5秒限制"
        
        # 计算响应时间统计
        response_times = [r["response_time"] for r in results if r["status_code"] == 200]
        if response_times:
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            
            # 单个查询响应时间应小于2秒
            assert max_response_time < 2, f"最大响应时间{max_response_time:.2f}秒，超过2秒限制"
            
            print(f"✅ PF-SR-01通过: 10个并发搜索，总耗时{total_time:.2f}秒")
            print(f"   平均响应时间: {avg_response_time:.2f}秒")
            print(f"   最大响应时间: {max_response_time:.2f}秒")
            print(f"   最小响应时间: {min_response_time:.2f}秒")
    
    def test_large_file_upload_performance(self, test_client: TestClient):
        """PF-UP-02: 大文件上传性能测试"""
        
        import tempfile
        
        # 创建10MB的PDF文件（大文件测试）
        large_content = b"%PDF-1.4\n"
        large_content += b"测试内容 " * (10 * 1024 * 1024 // 10)  # 10MB内容
        
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(large_content)
            tmp_path = Path(tmp.name)
        
        try:
            start_time = time.time()
            
            with open(tmp_path, "rb") as f:
                files = {"file": ("large_file.pdf", f, "application/pdf")}
                response = test_client.post("/upload", files=files)
            
            end_time = time.time()
            upload_time = end_time - start_time
            
            # 验证上传成功
            assert response.status_code == 200
            result = response.json()
            assert "task_id" in result
            
            # 性能要求：10MB文件上传应在30秒内完成
            assert upload_time < 30, f"大文件上传耗时{upload_time:.2f}秒，超过30秒限制"
            
            # 计算上传速度（MB/s）
            file_size_mb = 10
            upload_speed = file_size_mb / upload_time
            
            print(f"✅ PF-UP-02通过: 10MB文件上传，耗时{upload_time:.2f}秒，速度{upload_speed:.2f}MB/s")
            
        finally:
            tmp_path.unlink(missing_ok=True)
    
    def test_search_response_time_performance(self, test_client: TestClient):
        """PF-SR-02: 搜索响应时间性能测试"""
        
        # 测试不同复杂度的查询
        test_queries = [
            ("质量", "简单查询"),
            ("质量管理体系要求", "中等查询"),
            ("ISO 9001质量管理体系标准实施要求", "复杂查询"),
            ("质量方针制定程序和管理要求", "长查询"),
        ]
        
        performance_results = []
        
        for query, description in test_queries:
            # 多次测试取平均值
            response_times = []
            for _ in range(5):  # 每个查询测试5次
                start_time = time.time()
                response = test_client.get(f"/search?q={query}&top_k=10")
                end_time = time.time()
                
                if response.status_code == 200:
                    response_times.append(end_time - start_time)
            
            if response_times:
                avg_time = statistics.mean(response_times)
                max_time = max(response_times)
                min_time = min(response_times)
                
                performance_results.append({
                    "query": query,
                    "description": description,
                    "avg_time": avg_time,
                    "max_time": max_time,
                    "min_time": min_time
                })
                
                # 性能要求：平均响应时间应小于1秒
                assert avg_time < 1, f"'{query}' 平均响应时间{avg_time:.2f}秒，超过1秒限制"
                
                print(f"✅ {description}: 平均{avg_time:.2f}秒，最大{max_time:.2f}秒，最小{min_time:.2f}秒")
        
        print(f"✅ PF-SR-02通过: 搜索响应时间性能测试完成")
    
    def test_health_check_performance(self, test_client: TestClient):
        """PF-HC-01: 健康检查性能测试"""
        
        # 多次测试健康检查接口
        response_times = []
        for _ in range(20):  # 测试20次
            start_time = time.time()
            response = test_client.get("/health")
            end_time = time.time()
            
            if response.status_code == 200:
                response_times.append(end_time - start_time)
        
        if response_times:
            avg_time = statistics.mean(response_times)
            max_time = max(response_times)
            min_time = min(response_times)
            
            # 性能要求：健康检查应非常快速，平均响应时间小于0.1秒
            assert avg_time < 0.1, f"健康检查平均响应时间{avg_time:.2f}秒，超过0.1秒限制"
            
            print(f"✅ PF-HC-01通过: 健康检查性能")
            print(f"   平均响应时间: {avg_time:.4f}秒")
            print(f"   最大响应时间: {max_time:.4f}秒")
            print(f"   最小响应时间: {min_time:.4f}秒")
    
    def test_metrics_endpoint_performance(self, test_client: TestClient):
        """PF-MT-01: 监控指标性能测试"""
        
        # 测试监控指标接口性能
        response_times = []
        for _ in range(10):  # 测试10次
            start_time = time.time()
            response = test_client.get("/metrics")
            end_time = time.time()
            
            if response.status_code == 200:
                response_times.append(end_time - start_time)
        
        if response_times:
            avg_time = statistics.mean(response_times)
            max_time = max(response_times)
            
            # 性能要求：监控指标接口应快速响应，平均小于0.5秒
            assert avg_time < 0.5, f"监控指标平均响应时间{avg_time:.2f}秒，超过0.5秒限制"
            
            # 验证返回内容不为空
            response = test_client.get("/metrics")
            metrics_content = response.text
            assert len(metrics_content) > 0, "监控指标内容不应为空"
            
            print(f"✅ PF-MT-01通过: 监控指标性能")
            print(f"   平均响应时间: {avg_time:.4f}秒")
            print(f"   最大响应时间: {max_time:.4f}秒")
            print(f"   返回内容长度: {len(metrics_content)}字符")


class TestStressPerformance:
    """压力测试类"""
    
    def test_sustained_load_performance(self, test_client: TestClient):
        """ST-01: 持续负载性能测试"""
        
        # 模拟持续1分钟的负载测试
        duration = 60  # 秒
        start_time = time.time()
        request_count = 0
        success_count = 0
        response_times = []
        
        print(f"开始持续负载测试，持续时间: {duration}秒")
        
        while time.time() - start_time < duration:
            # 随机选择接口进行测试
            import random
            
            if random.random() < 0.6:  # 60%概率搜索
                query = random.choice(["质量", "管理", "体系", "要求", "标准"])
                start_req = time.time()
                response = test_client.get(f"/search?q={query}&top_k=3")
                end_req = time.time()
                
            elif random.random() < 0.8:  # 20%概率健康检查
                start_req = time.time()
                response = test_client.get("/health")
                end_req = time.time()
                
            else:  # 20%概率问答
                question = random.choice(["什么是质量方针？", "质量管理包括哪些内容？"])
                start_req = time.time()
                response = test_client.post("/ask", json={"question": question})
                end_req = time.time()
            
            request_count += 1
            if response.status_code == 200:
                success_count += 1
                response_times.append(end_req - start_req)
            
            # 短暂休息，避免过度压力
            time.sleep(0.1)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # 计算统计信息
        success_rate = success_count / request_count * 100
        avg_response_time = statistics.mean(response_times) if response_times else 0
        max_response_time = max(response_times) if response_times else 0
        
        # 压力测试要求
        assert success_rate >= 95, f"成功率{success_rate:.1f}%，低于95%要求"
        assert avg_response_time < 2, f"平均响应时间{avg_response_time:.2f}秒，超过2秒限制"
        assert max_response_time < 5, f"最大响应时间{max_response_time:.2f}秒，超过5秒限制"
        
        print(f"✅ ST-01通过: 持续负载测试")
        print(f"   总请求数: {request_count}")
        print(f"   成功请求: {success_count}")
        print(f"   成功率: {success_rate:.1f}%")
        print(f"   平均响应时间: {avg_response_time:.2f}秒")
        print(f"   最大响应时间: {max_response_time:.2f}秒")
        print(f"   总持续时间: {total_time:.2f}秒")


class TestScalabilityPerformance:
    """可扩展性测试类"""
    
    def test_large_dataset_search_performance(self, test_client: TestClient):
        """SC-01: 大数据集搜索性能测试"""
        
        # 注意：这个测试需要预先准备大量测试数据
        # 这里模拟大数据集搜索的性能要求
        
        large_queries = [
            "质量管理体系要求标准规范",
            "ISO 9001质量管理体系标准实施指南",
            "质量方针目标管理程序文件要求",
            "质量控制质量保证质量改进综合要求",
            "质量管理体系列标准规范要求指南"
        ]
        
        results = []
        for query in large_queries:
            start_time = time.time()
            response = test_client.get(f"/search?q={query}&top_k=20")
            end_time = time.time()
            
            results.append({
                "query": query,
                "response_time": end_time - start_time,
                "result_count": len(response.json()) if response.status_code == 200 else 0,
                "status_code": response.status_code
            })
        
        # 验证所有查询都成功
        success_results = [r for r in results if r["status_code"] == 200]
        assert len(success_results) >= 4, f"期望至少4个成功查询，实际{len(success_results)}个"
        
        # 性能要求：大数据集搜索应在3秒内完成
        max_response_time = max(r["response_time"] for r in success_results)
        assert max_response_time < 3, f"最大响应时间{max_response_time:.2f}秒，超过3秒限制"
        
        # 计算平均响应时间
        avg_response_time = statistics.mean(r["response_time"] for r in success_results)
        
        print(f"✅ SC-01通过: 大数据集搜索性能")
        print(f"   查询数量: {len(success_results)}")
        print(f"   平均响应时间: {avg_response_time:.2f}秒")
        print(f"   最大响应时间: {max_response_time:.2f}秒")
        print(f"   平均结果数量: {statistics.mean(r['result_count'] for r in success_results):.1f}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])