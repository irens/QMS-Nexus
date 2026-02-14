"""
集成测试运行脚本
兼容Windows PowerShell
"""
import subprocess
import sys
from pathlib import Path


def run_integration_tests():
    """运行集成测试"""
    print("🚀 开始运行QMS-Nexus集成测试...")
    
    # 测试目录
    test_dir = Path(__file__).parent
    
    # pytest命令参数
    pytest_args = [
        "pytest",
        str(test_dir),
        "-v",                    # 详细输出
        "-s",                    # 显示print输出
        "--tb=short",           # 简短错误信息
        "--asyncio-mode=auto",   # 自动处理异步测试
        "-m", "integration",    # 只运行集成测试
        "--log-cli-level=INFO",  # 日志级别
    ]
    
    print(f"📁 测试目录: {test_dir}")
    print(f"📝 测试命令: {' '.join(pytest_args)}")
    
    try:
        # 运行测试
        result = subprocess.run(pytest_args, capture_output=True, text=True)
        
        print("\n" + "="*60)
        print("📊 测试结果:")
        print("="*60)
        
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print("\n⚠️  错误信息:")
            print(result.stderr)
        
        print(f"\n🔚 测试退出码: {result.returncode}")
        
        if result.returncode == 0:
            print("✅ 所有集成测试通过！")
        else:
            print("❌ 部分测试失败")
            sys.exit(1)
            
    except FileNotFoundError:
        print("❌ 未找到pytest，请先安装: pip install pytest pytest-asyncio")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 运行测试失败: {e}")
        sys.exit(1)


def run_specific_test(test_file: str):
    """运行特定测试文件"""
    test_path = Path(__file__).parent / test_file
    
    if not test_path.exists():
        print(f"❌ 测试文件不存在: {test_path}")
        return
    
    print(f"🎯 运行特定测试: {test_file}")
    
    pytest_args = [
        "pytest",
        str(test_path),
        "-v",
        "-s",
        "--tb=short",
        "--asyncio-mode=auto",
        "--log-cli-level=INFO",
    ]
    
    try:
        subprocess.run(pytest_args)
    except Exception as e:
        print(f"❌ 运行测试失败: {e}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="QMS-Nexus集成测试运行器")
    parser.add_argument(
        "--file", 
        type=str, 
        help="运行特定测试文件（如 test_rag_integration.py）"
    )
    
    args = parser.parse_args()
    
    if args.file:
        run_specific_test(args.file)
    else:
        run_integration_tests()