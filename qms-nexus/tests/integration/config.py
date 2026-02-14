"""
集成测试配置文件
"""
import pytest

# 集成测试配置
INTEGRATION_TEST_CONFIG = {
    "max_upload_retries": 30,      # 最大重试次数
    "upload_retry_interval": 1,    # 重试间隔（秒）
    "test_query_timeout": 30,       # 查询超时时间
    "mock_llm_tokens": 150,         # Mock LLM响应的token数
    "embedding_dimension": 768,      # 向量嵌入维度
}

# pytest配置
def pytest_configure(config):
    """pytest配置钩子"""
    config.addinivalue_line(
        "markers", "integration: 标记集成测试"
    )
    config.addinivalue_line(
        "markers", "slow: 标记耗时测试"
    )

# 异步测试配置
pytest_plugins = ["pytest_asyncio"]

# 测试数据配置
TEST_PDF_CONTENT = """%PDF-1.4
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
/Length 200
>>
stream
BT
/F1 12 Tf
100 750 Td
(质量管理体系测试文档) Tj
T*
(本文件用于测试QMS-Nexus系统的文档处理功能) Tj
T*
(包含质量方针、目标设定、管理职责等核心内容) Tj
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
378
%%EOF"""