"""
集成测试运行器 - 基于测试用例设计
统一运行所有集成测试并生成报告
"""
import sys
import time
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any
import argparse


class IntegrationTestRunner:
    """集成测试运行器"""
    
    def __init__(self):
        self.test_root = Path(__file__).parent
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    def run_test_file(self, test_file: str, verbose: bool = False) -> Dict[str, Any]:
        """运行单个测试文件"""
        print(f"\n{'='*60}")
        print(f"运行测试文件: {test_file}")
        print(f"{'='*60}")
        
        cmd = [
            sys.executable, "-m", "pytest",
            str(self.test_root / test_file),
            "-v" if verbose else "-q",
            "--tb=short",
            "--json-report",
            "--json-report-file=-"  # 输出到stdout
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            # 解析pytest-json-report输出
            try:
                report_data = json.loads(result.stdout.split('\n')[-2])  # 获取JSON报告
            except:
                report_data = {
                    "summary": {
                        "passed": result.returncode == 0,
                        "failed": result.returncode != 0,
                        "total": 1
                    }
                }
            
            test_result = {
                "file": test_file,
                "status": "passed" if result.returncode == 0 else "failed",
                "return_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "summary": report_data.get("summary", {})
            }
            
            if result.returncode == 0:
                print(f"✅ {test_file} 测试通过")
            else:
                print(f"❌ {test_file} 测试失败")
                if verbose:
                    print(f"错误输出:\n{result.stderr}")
            
            return test_result
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_file} 测试超时")
            return {
                "file": test_file,
                "status": "timeout",
                "return_code": -1,
                "stdout": "",
                "stderr": "测试超时 (5分钟)"
            }
        except Exception as e:
            print(f"💥 {test_file} 测试异常: {e}")
            return {
                "file": test_file,
                "status": "error",
                "return_code": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    def run_all_tests(self, test_types: List[str] = None, priority: str = None, verbose: bool = False) -> Dict[str, Any]:
        """运行所有测试"""
        self.start_time = time.time()
        
        # 定义测试文件
        test_files = [
            "test_rag_integration.py",  # 基础集成测试
            "test_boundary.py",         # 边界值测试
            "test_equivalence.py",      # 等价类测试
            "test_exception.py",        # 异常处理测试
            "test_security.py",         # 安全测试
            "test_performance.py",      # 性能测试
        ]
        
        # 过滤测试类型
        if test_types:
            filtered_files = []
            for test_type in test_types:
                for test_file in test_files:
                    if test_type.lower() in test_file.lower():
                        filtered_files.append(test_file)
            test_files = list(set(filtered_files))
        
        print(f"\n🚀 开始运行集成测试...")
        print(f"测试文件: {', '.join(test_files)}")
        if priority:
            print(f"优先级过滤: {priority}")
        
        total_results = []
        
        for test_file in test_files:
            if not (self.test_root / test_file).exists():
                print(f"⚠️ 测试文件不存在: {test_file}")
                continue
            
            result = self.run_test_file(test_file, verbose)
            total_results.append(result)
            self.results[test_file] = result
        
        self.end_time = time.time()
        
        # 生成汇总报告
        summary = self.generate_summary(total_results)
        
        return {
            "summary": summary,
            "details": total_results,
            "duration": self.end_time - self.start_time
        }
    
    def generate_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成测试汇总"""
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        timeout_tests = 0
        error_tests = 0
        
        for result in results:
            summary = result.get("summary", {})
            if isinstance(summary, dict):
                passed_tests += summary.get("passed", 0)
                failed_tests += summary.get("failed", 0)
                total_tests += summary.get("total", 0)
            
            # 统计文件级别的状态
            if result["status"] == "passed":
                passed_tests += 1
            elif result["status"] == "failed":
                failed_tests += 1
            elif result["status"] == "timeout":
                timeout_tests += 1
            elif result["status"] == "error":
                error_tests += 1
        
        success_rate = (passed_tests / max(total_tests, 1)) * 100
        
        return {
            "total_files": len(results),
            "total_tests": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "timeout": timeout_tests,
            "error": error_tests,
            "success_rate": success_rate,
            "status": "passed" if failed_tests == 0 and error_tests == 0 and timeout_tests == 0 else "failed"
        }
    
    def print_report(self, results: Dict[str, Any]):
        """打印测试报告"""
        summary = results["summary"]
        duration = results["duration"]
        
        print(f"\n{'='*60}")
        print(f"🏁 集成测试执行报告")
        print(f"{'='*60}")
        print(f"执行时间: {duration:.2f}秒")
        print(f"测试文件: {summary['total_files']}个")
        print(f"总测试数: {summary['total_tests']}个")
        print(f"成功: {summary['passed']}个")
        print(f"失败: {summary['failed']}个")
        print(f"超时: {summary['timeout']}个")
        print(f"错误: {summary['error']}个")
        print(f"成功率: {summary['success_rate']:.1f}%")
        
        if summary["status"] == "passed":
            print(f"\n✅ 所有测试通过！")
        else:
            print(f"\n❌ 部分测试失败，请查看详细报告")
        
        print(f"\n{'='*60}")
        
        # 详细结果
        for result in results["details"]:
            status_icon = {
                "passed": "✅",
                "failed": "❌",
                "timeout": "⏰",
                "error": "💥"
            }.get(result["status"], "❓")
            
            print(f"{status_icon} {result['file']}: {result['status']}")
            
            if result["status"] != "passed" and result["stderr"]:
                print(f"   错误: {result['stderr'][:100]}...")
    
    def save_report(self, results: Dict[str, Any], output_file: str = None):
        """保存测试报告"""
        if not output_file:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            output_file = f"integration_test_report_{timestamp}.json"
        
        output_path = self.test_root / "reports" / output_file
        output_path.parent.mkdir(exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 测试报告已保存: {output_path}")
        return output_path


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="QMS-Nexus集成测试运行器")
    parser.add_argument(
        "--type", 
        nargs="+", 
        choices=["integration", "boundary", "equivalence", "exception", "security", "performance"],
        help="指定要运行的测试类型"
    )
    parser.add_argument(
        "--priority",
        choices=["P0", "P1", "P2"],
        help="按优先级过滤测试"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="显示详细输出"
    )
    parser.add_argument(
        "--output", "-o",
        help="输出报告文件路径"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="列出可用的测试文件"
    )
    
    args = parser.parse_args()
    
    runner = IntegrationTestRunner()
    
    if args.list:
        print("\n📋 可用的测试文件:")
        test_files = [
            "test_rag_integration.py - 基础集成测试",
            "test_boundary.py - 边界值测试", 
            "test_equivalence.py - 等价类测试",
            "test_exception.py - 异常处理测试",
            "test_security.py - 安全测试",
            "test_performance.py - 性能测试",
        ]
        for test_file in test_files:
            print(f"  {test_file}")
        return
    
    # 运行测试
    results = runner.run_all_tests(
        test_types=args.type,
        priority=args.priority,
        verbose=args.verbose
    )
    
    # 打印和保存报告
    runner.print_report(results)
    
    if args.output or True:  # 默认保存报告
        report_path = runner.save_report(results, args.output)
        
        # 生成HTML报告（可选）
        try:
            generate_html_report(results, report_path.with_suffix('.html'))
            print(f"📊 HTML报告已生成: {report_path.with_suffix('.html')}")
        except Exception as e:
            print(f"⚠️ HTML报告生成失败: {e}")
    
    # 返回适当的退出码
    if results["summary"]["status"] == "passed":
        sys.exit(0)
    else:
        sys.exit(1)


def generate_html_report(results: Dict[str, Any], output_path: Path):
    """生成HTML格式的测试报告"""
    summary = results["summary"]
    
    html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QMS-Nexus 集成测试报告</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .summary {{ display: flex; justify-content: space-around; margin: 20px 0; }}
        .metric {{ text-align: center; padding: 15px; border-radius: 8px; min-width: 120px; }}
        .metric.passed {{ background-color: #d4edda; color: #155724; }}
        .metric.failed {{ background-color: #f8d7da; color: #721c24; }}
        .metric.neutral {{ background-color: #d1ecf1; color: #0c5460; }}
        .details {{ margin-top: 30px; }}
        .test-result {{ margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; border-radius: 4px; }}
        .test-result.passed {{ border-left-color: #28a745; background-color: #f8fff9; }}
        .test-result.failed {{ border-left-color: #dc3545; background-color: #fff8f8; }}
        .test-result.timeout {{ border-left-color: #ffc107; background-color: #fffbf0; }}
        .test-result.error {{ border-left-color: #6c757d; background-color: #f8f9fa; }}
        .status-icon {{ font-size: 20px; margin-right: 10px; }}
        .timestamp {{ color: #666; font-size: 12px; }}
        pre {{ background-color: #f8f9fa; padding: 10px; border-radius: 4px; overflow-x: auto; font-size: 12px; }}
        .error-details {{ color: #dc3545; margin-top: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 QMS-Nexus 集成测试报告</h1>
            <p class="timestamp">生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>测试持续时间: {results.get('duration', 0):.2f}秒</p>
        </div>
        
        <div class="summary">
            <div class="metric {'passed' if summary['status'] == 'passed' else 'failed'}">
                <div class="status-icon">{'✅' if summary['status'] == 'passed' else '❌'}</div>
                <div><strong>总体状态</strong></div>
                <div>{'通过' if summary['status'] == 'passed' else '失败'}</div>
            </div>
            
            <div class="metric neutral">
                <div class="status-icon">📊</div>
                <div><strong>测试文件</strong></div>
                <div>{summary['total_files']}</div>
            </div>
            
            <div class="metric passed">
                <div class="status-icon">✅</div>
                <div><strong>成功</strong></div>
                <div>{summary['passed']}</div>
            </div>
            
            <div class="metric failed">
                <div class="status-icon">❌</div>
                <div><strong>失败</strong></div>
                <div>{summary['failed']}</div>
            </div>
            
            <div class="metric neutral">
                <div class="status-icon">📈</div>
                <div><strong>成功率</strong></div>
                <div>{summary['success_rate']:.1f}%</div>
            </div>
        </div>
        
        <div class="details">
            <h2>详细测试结果</h2>
            """
    
    for result in results["details"]:
        status_class = result["status"]
        status_icon = {
            "passed": "✅",
            "failed": "❌", 
            "timeout": "⏰",
            "error": "💥"
        }.get(result["status"], "❓")
        
        html_content += f"""
            <div class="test-result {status_class}">
                <div><span class="status-icon">{status_icon}</span><strong>{result['file']}</strong></div>
                <div>状态: {result['status']}</div>
                <div>返回码: {result['return_code']}</div>
                """
        
        if result["stderr"]:
            html_content += f"""
                <div class="error-details">
                    <strong>错误信息:</strong>
                    <pre>{result['stderr'][:500]}</pre>
                </div>
                """
        
        html_content += """
            </div>
            """
    
    html_content += """
        </div>
        
        <div style="margin-top: 30px; text-align: center; color: #666;">
            <p>QMS-Nexus 集成测试框架</p>
            <p>基于边界值分析、等价类划分、异常处理测试方法论</p>
        </div>
    </div>
</body>
</html>
    """
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)


if __name__ == "__main__":
    main()