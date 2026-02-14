# QMS-Nexus 集成测试文档

## 概述
集成测试验证从文件上传到最终问答的完整RAG链路，确保各组件协同工作正常。

## 测试结构

```
tests/integration/
├── __init__.py              # 包初始化
├── conftest.py              # 测试fixtures配置
├── config.py                # 测试配置
├── mock_llm.py              # LLM Mock配置
├── utils.py                 # 测试工具函数
├── run_tests.py             # 测试运行脚本
└── test_rag_integration.py  # 主要集成测试
```

## 测试流程

### 流程A：文档上传和处理
1. 调用 `/upload` 上传测试PDF
2. 轮询 `/tasks/{id}` 直到状态为 `completed`
3. 验证SQLite和ChromaDB中的数据存储

### 流程B：查询和回答
1. 调用 `/query` 提问
2. 验证返回结果包含 `text`、`source` 和 `tags`
3. 验证来源标注格式 `[来源：文件名, 第X页]`

### 流程C：用户反馈
1. 对回答调用 `/feedback`（赞/踩）
2. 验证SQLite中记录已更新

## Mock策略

- **LLM API调用**：使用Mock确保测试确定性和节省Token
- **向量嵌入**：返回固定维度的测试向量
- **数据库操作**：使用真实的SQLite和ChromaDB（内存模式）

## 运行测试

### 运行所有集成测试
```powershell
cd qms-nexus
python tests/integration/run_tests.py
```

### 运行特定测试文件
```powershell
python tests/integration/run_tests.py --file test_rag_integration.py
```

### 使用pytest直接运行
```powershell
pytest tests/integration -v -s --tb=short --asyncio-mode=auto
```

## 测试数据

测试使用简化的PDF文件，包含中文内容，用于验证文档解析和处理功能。

## 环境要求

- Python 3.10+
- pytest 和 pytest-asyncio
- FastAPI测试客户端
- 临时的SQLite和ChromaDB实例

## 注意事项

1. 测试使用内存数据库，不会影响生产环境
2. LLM调用被Mock，确保测试快速且确定
3. 测试完成后自动清理临时数据
4. 支持Windows PowerShell环境