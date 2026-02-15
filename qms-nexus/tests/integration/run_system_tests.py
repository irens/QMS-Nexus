"""
QMS-Nexus 系统测试执行器和报告生成器
"""
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import sys


class SystemTestRunner:
    """系统测试运行器"""
    
    def __init__(self):
        self.test_dir = Path("tests/integration")
        self.report_dir = Path("test_reports")
        self.report_dir.mkdir(exist_ok=True)
        
    def run_all_system_tests(self) -> Dict[str, Any]:
        """运行所有系统测试"""
        print("🚀 开始执行QMS-Nexus系统测试...")
        
        test_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_suites": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "errors": 0,
                "success_rate": 0.0
            }
        }
        
        # 定义测试套件
        test_suites = [
            {
                "name": "文件上传功能测试",
                "file": "test_system_upload_qa.py::TestFileUploadSystem",
                "description": "测试文件上传的各种场景"
            },
            {
                "name": "文档管理功能测试", 
                "file": "test_system_upload_qa.py::TestDocumentManagementSystem",
                "description": "测试文档列表、搜索、删除等功能"
            },
            {
                "name": "智能问答功能测试",
                "file": "test_system_upload_qa.py::TestIntelligentQASystem", 
                "description": "测试RAG问答系统的准确性和性能"
            },
            {
                "name": "标签管理功能测试",
                "file": "test_system_upload_qa.py::TestTagManagementSystem",
                "description": "测试标签创建、关联、筛选等功能"
            }
        ]
        
        # 运行每个测试套件
        for suite in test_suites:
            print(f"\n📋 执行测试套件: {suite['name']}")
            print(f"   描述: {suite['description']}")
            
            result = self.run_test_suite(suite['file'])
            test_results["test_suites"][suite['name']] = result
            
            # 更新总计
            test_results["summary"]["total_tests"] += result["total"]
            test_results["summary"]["passed"] += result["passed"]
            test_results["summary"]["failed"] += result["failed"]
            test_results["summary"]["errors"] += result["errors"]
        
        # 计算成功率
        if test_results["summary"]["total_tests"] > 0:
            test_results["summary"]["success_rate"] = (
                test_results["summary"]["passed"] / test_results["summary"]["total_tests"]
            ) * 100
        
        return test_results
    
    def run_test_suite(self, test_file: str) -> Dict[str, Any]:
        """运行单个测试套件"""
        cmd = [
            sys.executable, "-m", "pytest",
            f"tests/integration/{test_file}",
            "-v", "--tb=short"
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=".")
            
            # 解析测试结果
            output = result.stdout + result.stderr
            
            # 简单的结果解析
            passed = output.count("PASSED")
            failed = output.count("FAILED")
            errors = output.count("ERROR")
            total = passed + failed + errors
            
            suite_result = {
                "total": total,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "success_rate": (passed / total * 100) if total > 0 else 0,
                "output": output,
                "return_code": result.returncode
            }
            
            # 判断测试状态
            if failed == 0 and errors == 0 and passed > 0:
                suite_result["status"] = "✅ 通过"
            elif failed > 0:
                suite_result["status"] = "❌ 失败"
            else:
                suite_result["status"] = "⚠️ 异常"
                
            return suite_result
            
        except Exception as e:
            return {
                "total": 0,
                "passed": 0,
                "failed": 0,
                "errors": 1,
                "success_rate": 0,
                "output": f"运行测试时出错: {str(e)}",
                "return_code": -1,
                "status": "⚠️ 错误"
            }
    
    def generate_test_report(self, test_results: Dict[str, Any]) -> str:
        """生成测试报告"""
        report = []
        report.append("=" * 60)
        report.append("QMS-Nexus 系统测试报告")
        report.append("=" * 60)
        report.append(f"测试时间: {test_results['timestamp']}")
        report.append("")
        
        # 总体摘要
        summary = test_results["summary"]
        report.append("📊 测试摘要:")
        report.append(f"   总测试数: {summary['total_tests']}")
        report.append(f"   通过: {summary['passed']} ✅")
        report.append(f"   失败: {summary['failed']} ❌")
        report.append(f"   错误: {summary['errors']} ⚠️")
        report.append(f"   成功率: {summary['success_rate']:.1f}%")
        report.append("")
        
        # 各测试套件结果
        report.append("🧪 测试套件详情:")
        for suite_name, suite_result in test_results["test_suites"].items():
            report.append(f"\n{suite_name}:")
            report.append(f"   状态: {suite_result['status']}")
            report.append(f"   测试数: {suite_result['total']}")
            report.append(f"   通过: {suite_result['passed']}")
            report.append(f"   失败: {suite_result['failed']}")
            report.append(f"   成功率: {suite_result['success_rate']:.1f}%")
        
        # 测试建议
        report.append("\n💡 测试建议:")
        if summary["success_rate"] >= 95:
            report.append("   ✅ 系统测试表现优秀，建议继续完善边缘场景测试")
        elif summary["success_rate"] >= 80:
            report.append("   ⚠️ 系统测试基本通过，建议修复失败用例并加强异常处理")
        else:
            report.append("   ❌ 系统测试存在较多问题，建议优先修复核心功能缺陷")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)
    
    def save_report(self, test_results: Dict[str, Any], report_content: str):
        """保存测试报告"""
        # 保存JSON格式的结果
        json_file = self.report_dir / f"system_test_results_{int(time.time())}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)
        
        # 保存文本格式的报告
        report_file = self.report_dir / f"system_test_report_{int(time.time())}.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)
        
        print(f"\n📄 测试报告已保存:")
        print(f"   JSON结果: {json_file}")
        print(f"   文本报告: {report_file}")
        
        return json_file, report_file


def main():
    """主函数：执行系统测试"""
    print("🚀 启动QMS-Nexus系统测试执行器...")
    
    runner = SystemTestRunner()
    
    # 运行所有系统测试
    test_results = runner.run_all_system_tests()
    
    # 生成测试报告
    report_content = runner.generate_test_report(test_results)
    print("\n" + report_content)
    
    # 保存测试报告
    json_file, report_file = runner.save_report(test_results, report_content)
    
    # 返回测试结果状态
    success_rate = test_results["summary"]["success_rate"]
    if success_rate >= 95:
        print("\n🎉 系统测试通过！系统质量良好。")
        return 0
    elif success_rate >= 80:
        print("\n⚠️ 系统测试基本通过，但仍有改进空间。")
        return 1
    else:
        print("\n❌ 系统测试未通过，需要修复问题。")
        return 2


if __name__ == "__main__":
    sys.exit(main())