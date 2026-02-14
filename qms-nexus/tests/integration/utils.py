"""
集成测试工具函数
"""
import asyncio
import time
from typing import Any, Dict, Optional

import requests
from fastapi.testclient import TestClient


def poll_task_status(
    client: TestClient, 
    task_id: str, 
    max_retries: int = 30,
    interval: float = 1.0
) -> Dict[str, Any]:
    """
    轮询任务状态直到完成或失败
    
    Args:
        client: FastAPI测试客户端
        task_id: 任务ID
        max_retries: 最大重试次数
        interval: 轮询间隔（秒）
    
    Returns:
        最终任务状态
    
    Raises:
        TimeoutError: 任务处理超时
        RuntimeError: 任务处理失败
    """
    for attempt in range(max_retries):
        response = client.get(f"/upload/status/{task_id}")
        
        if response.status_code != 200:
            raise RuntimeError(f"获取任务状态失败: {response.status_code}")
        
        status_data = response.json()
        
        if status_data["status"] == "Completed":
            return status_data
        elif status_data["status"] == "Failed":
            error_msg = "任务处理失败"
            raise RuntimeError(f"任务处理失败: {error_msg}")
        
        time.sleep(interval)
    
    raise TimeoutError(f"任务处理超时（{max_retries}次重试）")


def validate_source_format(source: str) -> bool:
    """
    验证来源标注格式
    
    Args:
        source: 来源信息字符串
    
    Returns:
        格式是否正确
    """
    # 当前实现中source是简单的字符串
    return isinstance(source, str) and len(source) > 0


def create_test_pdf(tmp_path, filename: str = "test.pdf") -> str:
    """
    创建测试PDF文件
    
    Args:
        tmp_path: 临时目录路径
        filename: PDF文件名
    
    Returns:
        PDF文件路径
    """
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 100
>>
stream
BT
/F1 12 Tf
100 750 Td
(Test Document Content) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000053 00000 n 
0000000100 00000 n 
0000000178 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
278
%%EOF"""
    
    pdf_path = tmp_path / filename
    pdf_path.write_bytes(pdf_content)
    return str(pdf_path)


def assert_query_response_format(response_data: Dict[str, Any]) -> None:
    """
    验证查询响应格式
    
    Args:
        response_data: 查询响应数据
    
    Raises:
        AssertionError: 格式验证失败
    """
    # 检查必需字段
    required_fields = ["text", "source", "tags", "score"]
    for field in required_fields:
        assert field in response_data, f"缺少必需字段: {field}"
    
    # 验证回答内容
    assert isinstance(response_data["text"], str), "回答内容必须是字符串"
    assert len(response_data["text"]) > 0, "回答内容不能为空"
    
    # 验证来源信息
    assert isinstance(response_data["source"], str), "来源必须是字符串"
    assert len(response_data["source"]) > 0, "来源不应该为空"
    
    # 验证标签
    assert isinstance(response_data["tags"], list), "标签必须是列表"
    
    # 验证分数
    assert isinstance(response_data["score"], (int, float)), "分数必须是数字"
    assert 0 <= response_data["score"] <= 1, "分数必须在0-1之间"