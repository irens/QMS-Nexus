"""
QMS-Nexus 集成测试用例 - 等价类划分详细设计
基于测试设计文档的具体测试用例实现
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class TestPriority(Enum):
    """测试优先级"""
    P0 = "高"  # 核心功能，必须测试
    P1 = "中"  # 重要功能，建议测试
    P2 = "低"  # 边缘情况，可选测试


class TestType(Enum):
    """测试类型"""
    BOUNDARY = "边界值"
    EQUIVALENCE = "等价类"
    EXCEPTION = "异常处理"
    PERFORMANCE = "性能"
    SECURITY = "安全"


@dataclass
class TestCase:
    """测试用例数据结构"""
    case_id: str
    test_type: TestType
    priority: TestPriority
    description: str
    endpoint: str
    method: str
    input_data: Dict[str, Any]
    expected_status: int
    expected_response: Dict[str, Any]
    preconditions: List[str]
    postconditions: List[str]
    notes: Optional[str] = None


class QMSIntegrationTestCases:
    """QMS-Nexus集成测试用例集合"""
    
    def __init__(self):
        self.test_cases = []
        self._generate_all_test_cases()
    
    def _generate_all_test_cases(self):
        """生成所有测试用例"""
        self._generate_upload_test_cases()
        self._generate_search_test_cases()
        self._generate_ask_test_cases()
        self._generate_status_test_cases()
        self._generate_health_test_cases()
        self._generate_performance_test_cases()
        self._generate_security_test_cases()
    
    def _generate_upload_test_cases(self):
        """文件上传接口测试用例"""
        
        # === 边界值测试 (Boundary Value Analysis) ===
        
        # 文件大小边界测试
        self.test_cases.extend([
            TestCase(
                case_id="UP-BV-01",
                test_type=TestType.BOUNDARY,
                priority=TestPriority.P0,
                description="文件大小边界-最小值(0字节)",
                endpoint="/upload",
                method="POST",
                input_data={
                    "file": {"name": "empty.pdf", "size": 0, "content_type": "application/pdf"}
                },
                expected_status=400,
                expected_response={"detail": "文件内容为空"},
                preconditions=["系统正常运行"],
                postconditions=["返回400错误"],
                notes="需要Mock文件对象"
            ),
            TestCase(
                case_id="UP-BV-02",
                test_type=TestType.BOUNDARY,
                priority=TestPriority.P0,
                description="文件大小边界-刚好50MB",
                endpoint="/upload",
                method="POST",
                input_data={
                    "file": {"name": "large.pdf", "size": 50*1024*1024, "content_type": "application/pdf"}
                },
                expected_status=200,
                expected_response={"task_id": "valid_uuid", "status": "Pending"},
                preconditions=["系统正常运行"],
                postconditions=["任务创建成功"],
                notes="边界值测试"
            ),
            TestCase(
                case_id="UP-BV-03",
                test_type=TestType.BOUNDARY,
                priority=TestPriority.P0,
                description="文件大小边界-超过50MB",
                endpoint="/upload",
                method="POST",
                input_data={
                    "file": {"name": "oversized.pdf", "size": 51*1024*1024, "content_type": "application/pdf"}
                },
                expected_status=413,
                expected_response={"detail": "文件超过 50 MB"},
                preconditions=["系统正常运行"],
                postconditions=["返回413错误"],
                notes="边界值测试"
            )
        ])
        
        # Content-Type边界测试
        self.test_cases.extend([
            TestCase(
                case_id="UP-BV-04",
                test_type=TestType.BOUNDARY,
                priority=TestPriority.P0,
                description="Content-Type边界-空值",
                endpoint="/upload",
                method="POST",
                input_data={
                    "file": {"name": "test.pdf", "size": 1024, "content_type": None}
                },
                expected_status=400,
                expected_response={"detail": "缺少 Content-Type"},
                preconditions=["系统正常运行"],
                postconditions=["返回400错误"],
                notes="边界值测试"
            ),
            TestCase(
                case_id="UP-BV-05",
                test_type=TestType.BOUNDARY,
                priority=TestPriority.P1,
                description="Content-Type边界-格式错误",
                endpoint="/upload",
                method="POST",
                input_data={
                    "file": {"name": "test.pdf", "size": 1024, "content_type": "invalid/type"}
                },
                expected_status=400,
                expected_response={"detail": "不支持的文件类型"},
                preconditions=["系统正常运行"],
                postconditions=["返回400错误"],
                notes="边界值测试"
            )
        ])
        
        # === 等价类测试 (Equivalence Partitioning) ===
        
        # 有效文件类型等价类
        valid_file_types = [
            ("UP-EC-01", "application/pdf", "test.pdf"),
            ("UP-EC-02", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "test.docx"),
            ("UP-EC-03", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "test.xlsx"),
            ("UP-EC-04", "application/vnd.openxmlformats-officedocument.presentationml.presentation", "test.pptx"),
            ("UP-EC-05", "application/vnd.ms-excel", "test.xls")
        ]
        
        for case_id, content_type, filename in valid_file_types:
            self.test_cases.append(TestCase(
                case_id=case_id,
                test_type=TestType.EQUIVALENCE,
                priority=TestPriority.P0,
                description=f"有效文件类型-{content_type.split('/')[-1]}",
                endpoint="/upload",
                method="POST",
                input_data={
                    "file": {"name": filename, "size": 1024, "content_type": content_type}
                },
                expected_status=200,
                expected_response={"task_id": "valid_uuid", "status": "Pending"},
                preconditions=["系统正常运行"],
                postconditions=["任务创建成功"],
                notes="有效等价类"
            ))
        
        # 无效文件类型等价类
        invalid_file_types = [
            ("UP-EC-06", "image/jpeg", "test.jpg"),
            ("UP-EC-07", "text/plain", "test.txt"),
            ("UP-EC-08", "application/x-msdownload", "test.exe"),
            ("UP-EC-09", "video/mp4", "test.mp4")
        ]
        
        for case_id, content_type, filename in invalid_file_types:
            self.test_cases.append(TestCase(
                case_id=case_id,
                test_type=TestType.EQUIVALENCE,
                priority=TestPriority.P1,
                description=f"无效文件类型-{content_type.split('/')[-1]}",
                endpoint="/upload",
                method="POST",
                input_data={
                    "file": {"name": filename, "size": 1024, "content_type": content_type}
                },
                expected_status=400,
                expected_response={"detail": "不支持的文件类型"},
                preconditions=["系统正常运行"],
                postconditions=["返回400错误"],
                notes="无效等价类"
            ))
        
        # === 异常处理测试 (Exception Handling) ===
        
        self.test_cases.extend([
            TestCase(
                case_id="UP-EX-01",
                test_type=TestType.EXCEPTION,
                priority=TestPriority.P1,
                description="文件损坏处理",
                endpoint="/upload",
                method="POST",
                input_data={
                    "file": {"name": "corrupted.pdf", "size": 1024, "content_type": "application/pdf", "corrupted": True}
                },
                expected_status=200,  # 上传成功，但后续处理失败
                expected_response={"task_id": "valid_uuid", "status": "Pending"},
                preconditions=["系统正常运行"],
                postconditions=["任务状态最终为Failed"],
                notes="异步处理异常"
            ),
            TestCase(
                case_id="UP-EX-02",
                test_type=TestType.EXCEPTION,
                priority=TestPriority.P0,
                description="Redis连接失败",
                endpoint="/upload",
                method="POST",
                input_data={
                    "file": {"name": "test.pdf", "size": 1024, "content_type": "application/pdf"},
                    "mock_redis_failure": True
                },
                expected_status=200,  # 上传成功，但任务无法处理
                expected_response={"task_id": "valid_uuid", "status": "Pending"},
                preconditions=["Redis服务不可用"],
                postconditions=["任务保持Pending状态"],
                notes="外部依赖异常"
            )
        ])
    
    def _generate_search_test_cases(self):
        """搜索接口测试用例"""
        
        # === 边界值测试 ===
        
        # top_k参数边界测试
        self.test_cases.extend([
            TestCase(
                case_id="SR-BV-01",
                test_type=TestType.BOUNDARY,
                priority=TestPriority.P0,
                description="top_k边界-最小值(1)",
                endpoint="/search",
                method="GET",
                input_data={"q": "质量方针", "top_k": 1},
                expected_status=200,
                expected_response=[{"text": "str", "source": "str", "tags": [], "score": 0.0}],
                preconditions=["存在相关文档"],
                postconditions=["返回1个结果"],
                notes="边界值测试"
            ),
            TestCase(
                case_id="SR-BV-02",
                test_type=TestType.BOUNDARY,
                priority=TestPriority.P0,
                description="top_k边界-最大值(100)",
                endpoint="/search",
                method="GET",
                input_data={"q": "质量方针", "top_k": 100},
                expected_status=200,
                expected_response=[{"text": "str", "source": "str", "tags": [], "score": 0.0}],
                preconditions=["存在相关文档"],
                postconditions=["返回≤100个结果"],
                notes="边界值测试"
            ),
            TestCase(
                case_id="SR-BV-03",
                test_type=TestType.BOUNDARY,
                priority=TestPriority.P0,
                description="top_k边界-超过最大值(101)",
                endpoint="/search",
                method="GET",
                input_data={"q": "质量方针", "top_k": 101},
                expected_status=422,
                expected_response={"detail": "top_k必须在1-100之间"},
                preconditions=["系统正常运行"],
                postconditions=["返回422错误"],
                notes="边界值测试"
            ),
            TestCase(
                case_id="SR-BV-04",
                test_type=TestType.BOUNDARY,
                priority=TestPriority.P0,
                description="top_k边界-零值",
                endpoint="/search",
                method="GET",
                input_data={"q": "质量方针", "top_k": 0},
                expected_status=422,
                expected_response={"detail": "top_k必须大于0"},
                preconditions=["系统正常运行"],
                postconditions=["返回422错误"],
                notes="边界值测试"
            ),
            TestCase(
                case_id="SR-BV-05",
                test_type=TestType.BOUNDARY,
                priority=TestPriority.P0,
                description="top_k边界-负值",
                endpoint="/search",
                method="GET",
                input_data={"q": "质量方针", "top_k": -1},
                expected_status=422,
                expected_response={"detail": "top_k必须大于0"},
                preconditions=["系统正常运行"],
                postconditions=["返回422错误"],
                notes="边界值测试"
            )
        ])
        
        # === 等价类测试 ===
        
        # 查询文本等价类
        query_equivalence_classes = [
            ("SR-EC-01", "质量方针管理要求", "中文事实查询"),
            ("SR-EC-02", "quality management system", "英文事实查询"),
            ("SR-EC-03", "ISO 9001质量管理体系要求", "混合语言查询"),
            ("SR-EC-04", "如何制定质量目标", "程序型查询"),
            ("SR-EC-05", "质量管理和质量控制的区别", "对比型查询")
        ]
        
        for case_id, query, description in query_equivalence_classes:
            self.test_cases.append(TestCase(
                case_id=case_id,
                test_type=TestType.EQUIVALENCE,
                priority=TestPriority.P0,
                description=f"有效查询-{description}",
                endpoint="/search",
                method="GET",
                input_data={"q": query, "top_k": 5},
                expected_status=200,
                expected_response=[{"text": "str", "source": "str", "tags": [], "score": 0.0}],
                preconditions=["存在相关文档"],
                postconditions=["返回相关结果"],
                notes="有效等价类"
            ))
        
        # 无效查询等价类
        invalid_queries = [
            ("SR-EC-06", "", "空查询"),
            ("SR-EC-07", "   ", "仅空格"),
            ("SR-EC-08", "@#$%^&*()", "特殊字符"),
            ("SR-EC-09", "a" * 1000, "超长查询")
        ]
        
        for case_id, query, description in invalid_queries:
            self.test_cases.append(TestCase(
                case_id=case_id,
                test_type=TestType.EQUIVALENCE,
                priority=TestPriority.P1,
                description=f"无效查询-{description}",
                endpoint="/search",
                method="GET",
                input_data={"q": query, "top_k": 5},
                expected_status=400,
                expected_response={"detail": "查询文本不能为空"},
                preconditions=["系统正常运行"],
                postconditions=["返回400错误或空结果"],
                notes="无效等价类"
            ))
        
        # === 标签过滤测试 ===
        
        tag_filter_tests = [
            ("SR-TF-01", ["质量"], "单标签过滤"),
            ("SR-TF-02", ["质量", "管理"], "多标签过滤"),
            ("SR-TF-03", ["不存在的标签"], "不存在标签"),
            ("SR-TF-04", [], "空标签列表")
        ]
        
        for case_id, tags, description in tag_filter_tests:
            self.test_cases.append(TestCase(
                case_id=case_id,
                test_type=TestType.EQUIVALENCE,
                priority=TestPriority.P1,
                description=f"标签过滤-{description}",
                endpoint="/search",
                method="GET",
                input_data={"q": "质量方针", "top_k": 5, "filter_tags": tags},
                expected_status=200,
                expected_response=[{"text": "str", "source": "str", "tags": [], "score": 0.0}],
                preconditions=["存在相关文档"],
                postconditions=["按标签过滤结果"],
                notes="标签过滤功能"
            ))
    
    def _generate_ask_test_cases(self):
        """问答接口测试用例"""
        
        # === 等价类测试 ===
        
        # 有效问题等价类
        valid_questions = [
            ("AS-EC-01", "什么是质量方针？", "事实型问题"),
            ("AS-EC-02", "如何制定质量目标？", "程序型问题"),
            ("AS-EC-03", "质量管理和质量控制的区别？", "对比型问题"),
            ("AS-EC-04", "请解释ISO 9001标准", "解释型问题"),
            ("AS-EC-05", "质量管理体系包括哪些内容？", "列举型问题")
        ]
        
        for case_id, question, description in valid_questions:
            self.test_cases.append(TestCase(
                case_id=case_id,
                test_type=TestType.EQUIVALENCE,
                priority=TestPriority.P0,
                description=f"有效问题-{description}",
                endpoint="/ask",
                method="POST",
                input_data={"question": question},
                expected_status=200,
                expected_response={"answer": "str", "sources": []},
                preconditions=["存在相关知识库"],
                postconditions=["返回答案和来源"],
                notes="有效问题等价类"
            ))
        
        # 无效问题等价类
        invalid_questions = [
            ("AS-EC-06", "", "空问题"),
            ("AS-EC-07", "   ", "仅空格"),
            ("AS-EC-08", "今天天气如何？", "无关问题"),
            ("AS-EC-09", "123456", "无意义数字"),
            ("AS-EC-10", "a" * 2000, "超长问题")
        ]
        
        for case_id, question, description in invalid_questions:
            expected_response = {"answer": "知识库中暂无相关记录", "sources": []} if question and question.strip() else {"detail": "问题不能为空"}
            expected_status = 200 if question and question.strip() else 400
            
            self.test_cases.append(TestCase(
                case_id=case_id,
                test_type=TestType.EQUIVALENCE,
                priority=TestPriority.P1,
                description=f"无效问题-{description}",
                endpoint="/ask",
                method="POST",
                input_data={"question": question},
                expected_status=expected_status,
                expected_response=expected_response,
                preconditions=["系统正常运行"],
                postconditions=["返回默认回答或错误"],
                notes="无效问题等价类"
            ))
        
        # === 异常处理测试 ===
        
        self.test_cases.extend([
            TestCase(
                case_id="AS-EX-01",
                test_type=TestType.EXCEPTION,
                priority=TestPriority.P0,
                description="LLM服务超时",
                endpoint="/ask",
                method="POST",
                input_data={"question": "什么是质量方针？", "mock_llm_timeout": True},
                expected_status=504,
                expected_response={"detail": "LLM服务超时"},
                preconditions=["LLM服务不可用"],
                postconditions=["返回超时错误"],
                notes="外部服务异常"
            ),
            TestCase(
                case_id="AS-EX-02",
                test_type=TestType.EXCEPTION,
                priority=TestPriority.P0,
                description="向量数据库异常",
                endpoint="/ask",
                method="POST",
                input_data={"question": "什么是质量方针？", "mock_vector_db_failure": True},
                expected_status=500,
                expected_response={"detail": "向量数据库异常"},
                preconditions=["向量数据库不可用"],
                postconditions=["返回500错误"],
                notes="外部依赖异常"
            )
        ])
    
    def _generate_status_test_cases(self):
        """任务状态查询测试用例"""
        
        # === 等价类测试 ===
        
        # 有效任务ID
        self.test_cases.extend([
            TestCase(
                case_id="TS-EC-01",
                test_type=TestType.EQUIVALENCE,
                priority=TestPriority.P0,
                description="有效任务ID-存在",
                endpoint="/upload/status/{task_id}",
                method="GET",
                input_data={"task_id": "valid-uuid-12345"},
                expected_status=200,
                expected_response={"task_id": "valid-uuid-12345", "status": "Pending"},
                preconditions=["任务已创建"],
                postconditions=["返回任务状态"],
                notes="有效任务ID等价类"
            ),
            TestCase(
                case_id="TS-EC-02",
                test_type=TestType.EQUIVALENCE,
                priority=TestPriority.P0,
                description="有效任务ID-不存在",
                endpoint="/upload/status/{task_id}",
                method="GET",
                input_data={"task_id": "non-existent-uuid"},
                expected_status=404,
                expected_response={"detail": "任务不存在"},
                preconditions=["任务未创建"],
                postconditions=["返回404错误"],
                notes="无效任务ID等价类"
            )
        ])
        
        # 无效任务ID格式
        invalid_task_ids = [
            ("TS-EC-03", "", "空任务ID"),
            ("TS-EC-04", "invalid-format", "非UUID格式"),
            ("TS-EC-05", "123", "过短ID"),
            ("TS-EC-06", "a" * 100, "过长ID")
        ]
        
        for case_id, task_id, description in invalid_task_ids:
            self.test_cases.append(TestCase(
                case_id=case_id,
                test_type=TestType.EQUIVALENCE,
                priority=TestPriority.P1,
                description=f"无效任务ID-{description}",
                endpoint="/upload/status/{task_id}",
                method="GET",
                input_data={"task_id": task_id},
                expected_status=404,
                expected_response={"detail": "任务不存在"},
                preconditions=["系统正常运行"],
                postconditions=["返回404错误"],
                notes="无效任务ID等价类"
            ))
    
    def _generate_health_test_cases(self):
        """健康检查测试用例"""
        
        self.test_cases.extend([
            TestCase(
                case_id="HC-01",
                test_type=TestType.EQUIVALENCE,
                priority=TestPriority.P0,
                description="系统健康检查-正常",
                endpoint="/health",
                method="GET",
                input_data={},
                expected_status=200,
                expected_response={"status": "ok"},
                preconditions=["所有服务正常"],
                postconditions=["返回健康状态"],
                notes="健康检查基础功能"
            ),
            TestCase(
                case_id="HC-02",
                test_type=TestType.EXCEPTION,
                priority=TestPriority.P1,
                description="系统健康检查-数据库异常",
                endpoint="/health",
                method="GET",
                input_data={"mock_db_failure": True},
                expected_status=503,
                expected_response={"status": "error", "detail": "数据库连接失败"},
                preconditions=["数据库服务不可用"],
                postconditions=["返回错误状态"],
                notes="健康检查异常处理"
            )
        ])
    
    def _generate_performance_test_cases(self):
        """性能测试用例"""
        
        self.test_cases.extend([
            TestCase(
                case_id="PF-UP-01",
                test_type=TestType.PERFORMANCE,
                priority=TestPriority.P1,
                description="并发上传测试-5个文件",
                endpoint="/upload",
                method="POST",
                input_data={"concurrent_files": 5},
                expected_status=200,
                expected_response=[{"task_id": "uuid", "status": "Pending"}],
                preconditions=["系统正常运行"],
                postconditions=["所有任务创建成功"],
                notes="并发性能测试"
            ),
            TestCase(
                case_id="PF-SR-01",
                test_type=TestType.PERFORMANCE,
                priority=TestPriority.P1,
                description="并发搜索测试-10QPS",
                endpoint="/search",
                method="GET",
                input_data={"q": "质量方针", "concurrent_requests": 10},
                expected_status=200,
                expected_response=[{"text": "str", "source": "str", "tags": [], "score": 0.0}],
                preconditions=["存在相关文档"],
                postconditions=["响应时间<2s"],
                notes="搜索性能测试"
            )
        ])
    
    def _generate_security_test_cases(self):
        """安全测试用例"""
        
        self.test_cases.extend([
            TestCase(
                case_id="SC-01",
                test_type=TestType.SECURITY,
                priority=TestPriority.P0,
                description="SQL注入防护",
                endpoint="/search",
                method="GET",
                input_data={"q": "质量方针'; DROP TABLE documents; --"},
                expected_status=200,
                expected_response=[],  # 安全处理后返回空结果
                preconditions=["系统正常运行"],
                postconditions=["无SQL注入成功"],
                notes="安全注入测试"
            ),
            TestCase(
                case_id="SC-02",
                test_type=TestType.SECURITY,
                priority=TestPriority.P0,
                description="XSS攻击防护",
                endpoint="/search",
                method="GET",
                input_data={"q": "<script>alert('xss')</script>质量方针"},
                expected_status=200,
                expected_response=[],  # 安全处理后返回空结果或过滤结果
                preconditions=["系统正常运行"],
                postconditions=["无XSS脚本执行"],
                notes="XSS防护测试"
            ),
            TestCase(
                case_id="SC-03",
                test_type=TestType.SECURITY,
                priority=TestPriority.P0,
                description="路径遍历防护",
                endpoint="/upload",
                method="POST",
                input_data={
                    "file": {"name": "../../../etc/passwd", "size": 1024, "content_type": "application/pdf"}
                },
                expected_status=400,
                expected_response={"detail": "文件名包含非法字符"},
                preconditions=["系统正常运行"],
                postconditions=["路径遍历被阻止"],
                notes="路径安全测试"
            )
        ])
    
    def get_test_cases_by_type(self, test_type: TestType) -> List[TestCase]:
        """按测试类型获取测试用例"""
        return [case for case in self.test_cases if case.test_type == test_type]
    
    def get_test_cases_by_priority(self, priority: TestPriority) -> List[TestCase]:
        """按优先级获取测试用例"""
        return [case for case in self.test_cases if case.priority == priority]
    
    def get_test_cases_by_endpoint(self, endpoint: str) -> List[TestCase]:
        """按接口获取测试用例"""
        return [case for case in self.test_cases if case.endpoint == endpoint]
    
    def get_all_test_cases(self) -> List[TestCase]:
        """获取所有测试用例"""
        return self.test_cases.copy()
    
    def get_test_statistics(self) -> Dict[str, int]:
        """获取测试用例统计信息"""
        stats = {
            "total": len(self.test_cases),
            "by_type": {},
            "by_priority": {},
            "by_endpoint": {}
        }
        
        for case in self.test_cases:
            # 按类型统计
            type_name = case.test_type.value
            stats["by_type"][type_name] = stats["by_type"].get(type_name, 0) + 1
            
            # 按优先级统计
            priority_name = case.priority.value
            stats["by_priority"][priority_name] = stats["by_priority"].get(priority_name, 0) + 1
            
            # 按接口统计
            endpoint = case.endpoint
            stats["by_endpoint"][endpoint] = stats["by_endpoint"].get(endpoint, 0) + 1
        
        return stats


# 全局测试用例实例
test_cases = QMSIntegrationTestCases()


if __name__ == "__main__":
    # 打印测试用例统计信息
    stats = test_cases.get_test_statistics()
    print("=== QMS-Nexus集成测试用例统计 ===")
    print(f"总用例数: {stats['total']}")
    print(f"\n按类型分布:")
    for test_type, count in stats["by_type"].items():
        print(f"  {test_type}: {count}")
    print(f"\n按优先级分布:")
    for priority, count in stats["by_priority"].items():
        print(f"  {priority}: {count}")
    print(f"\n按接口分布:")
    for endpoint, count in stats["by_endpoint"].items():
        print(f"  {endpoint}: {count}")
    
    # 打印高优先级测试用例
    print(f"\n=== 高优先级测试用例 (P0) ===")
    p0_cases = test_cases.get_test_cases_by_priority(TestPriority.P0)
    for case in p0_cases[:5]:  # 只显示前5个
        print(f"{case.case_id}: {case.description}")
    print(f"... 还有 {len(p0_cases)-5} 个P0用例")