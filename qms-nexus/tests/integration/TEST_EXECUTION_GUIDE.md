# QMS-Nexus 集成测试用例执行指南

## 📋 测试用例概览

基于边界值分析、等价类划分和异常处理测试方法论，设计了**45个**全面的集成测试用例：

- **边界值测试**: 15个用例 (33%)
- **等价类测试**: 20个用例 (44%) 
- **异常处理测试**: 5个用例 (11%)
- **性能测试**: 2个用例 (4%)
- **安全测试**: 3个用例 (7%)

## 🎯 测试优先级分布

- **P0 (高优先级)**: 28个用例 (62%) - 核心功能
- **P1 (中优先级)**: 14个用例 (31%) - 重要功能  
- **P2 (低优先级)**: 3个用例 (7%) - 边缘情况

## 🔧 接口测试覆盖

| 接口 | 用例数 | 覆盖类型 |
|------|--------|----------|
| `/upload` | 18个 | 边界值、等价类、异常、安全 |
| `/upload/status/{id}` | 7个 | 等价类、边界值 |
| `/search` | 13个 | 边界值、等价类、标签过滤、安全 |
| `/ask` | 7个 | 等价类、异常处理 |

## 🚀 快速开始

### 1. 运行所有测试
```powershell
python tests/integration/run_tests.py
```

### 2. 按类型运行测试
```powershell
# 边界值测试
python -m pytest tests/integration/test_boundary.py -v

# 等价类测试  
python -m pytest tests/integration/test_equivalence.py -v

# 异常处理测试
python -m pytest tests/integration/test_exception.py -v

# 安全测试
python -m pytest tests/integration/test_security.py -v
```

### 3. 按优先级运行测试
```powershell
# 高优先级测试 (P0)
python -m pytest tests/integration -k "P0" -v

# 中优先级测试 (P1)
python -m pytest tests/integration -k "P1" -v
```

### 4. 按接口运行测试
```powershell
# 上传接口测试
python -m pytest tests/integration -k "upload" -v

# 搜索接口测试
python -m pytest tests/integration -k "search" -v

# 问答接口测试
python -m pytest tests/integration -k "ask" -v
```

## 📊 核心测试场景

### 文件上传测试矩阵

| 测试维度 | 测试点 | 用例ID | 预期结果 |
|----------|--------|--------|----------|
| **文件大小** | 0字节 | UP-BV-01 | 400错误 |
| | 50MB边界 | UP-BV-02 | 200成功 |
| | 51MB超大 | UP-BV-03 | 413错误 |
| **文件类型** | PDF(有效) | UP-EC-01 | 200成功 |
| | DOCX(有效) | UP-EC-02 | 200成功 |
| | JPG(无效) | UP-EC-06 | 400错误 |
| | EXE(无效) | UP-EC-08 | 400错误 |
| **Content-Type** | 空值 | UP-BV-04 | 400错误 |
| | 无效格式 | UP-BV-05 | 400错误 |

### 搜索测试矩阵

| 测试维度 | 测试点 | 用例ID | 预期结果 |
|----------|--------|--------|----------|
| **top_k参数** | 最小值(1) | SR-BV-01 | 返回1个结果 |
| | 最大值(100) | SR-BV-02 | 返回≤100结果 |
| | 超过最大(101) | SR-BV-03 | 422错误 |
| | 零值 | SR-BV-04 | 422错误 |
| | 负值 | SR-BV-05 | 422错误 |
| **查询类型** | 中文事实 | SR-EC-01 | 返回中文结果 |
| | 英文事实 | SR-EC-02 | 返回英文结果 |
| | 混合语言 | SR-EC-03 | 返回混合结果 |
| | 空查询 | SR-EC-06 | 400错误 |
| | 特殊字符 | SR-EC-08 | 空结果/错误 |
| **标签过滤** | 单标签 | SR-TF-01 | 精确过滤 |
| | 多标签 | SR-TF-02 | 或条件过滤 |
| | 不存在标签 | SR-TF-03 | 返回空结果 |

### 问答测试矩阵

| 测试维度 | 测试点 | 用例ID | 预期结果 |
|----------|--------|--------|----------|
| **问题类型** | 事实型 | AS-EC-01 | 具体定义 |
| | 程序型 | AS-EC-02 | 步骤说明 |
| | 对比型 | AS-EC-03 | 对比分析 |
| | 解释型 | AS-EC-04 | 详细解释 |
| | 列举型 | AS-EC-05 | 列表回答 |
| **无效问题** | 空问题 | AS-EC-06 | 400错误 |
| | 无关问题 | AS-EC-08 | 默认回答 |
| | 超长问题 | AS-EC-10 | 截断处理 |

## 🔍 安全测试重点

### 注入攻击防护
- **SQL注入**: SC-01 测试恶意SQL语句
- **XSS攻击**: SC-02 测试脚本注入  
- **路径遍历**: SC-03 测试目录穿越

### 输入验证
- 文件名特殊字符过滤
- 查询参数长度限制
- 文件类型白名单验证

## ⚡ 性能测试基准

### 并发性能要求
- **文件上传**: 5个并发文件，全部成功处理
- **搜索查询**: 10 QPS，响应时间<2秒
- **大文件处理**: 50MB文件，处理时间<30秒

### 资源使用限制
- 内存使用: <1GB (单并发)
- CPU使用: <80% (峰值)
- 磁盘I/O: 合理范围内

## 🛠️ 测试数据准备

### 测试文件集合
```
tests/integration/test_data/
├── boundary/
│   ├── empty.pdf              # 0字节文件
│   ├── exactly_50mb.pdf       # 刚好50MB
│   └── oversized_51mb.pdf   # 51MB超大文件
├── equivalence/
│   ├── valid_pdf.pdf          # 标准PDF
│   ├── valid_docx.docx        # 标准Word
│   ├── valid_xlsx.xlsx        # 标准Excel
│   └── invalid_jpg.jpg      # 无效图片文件
├── security/
│   ├── sql_injection.pdf      # 包含SQL注入
│   ├── xss_script.pdf         # 包含XSS脚本
│   └── path_traversal.pdf     # 路径遍历文件名
└── special/
    ├── corrupted.pdf          # 损坏的PDF
    ├── chinese_content.pdf    # 中文内容
    ├── english_content.pdf    # 英文内容
    └── mixed_content.pdf      # 混合内容
```

### 测试查询语料
```
tests/integration/test_queries/
├── valid/
│   ├── factual_questions.txt  # 事实型问题
│   ├── procedural_questions.txt # 程序型问题
│   └── comparative_questions.txt # 对比型问题
├── invalid/
│   ├── empty_queries.txt      # 空查询
│   ├── special_chars.txt      # 特殊字符
│   └── injection_attempts.txt # 注入攻击
└── edge/
    ├── very_long_queries.txt   # 超长查询
    └── unicode_queries.txt     # Unicode字符
```

## 📈 测试执行策略

### 阶段1: 冒烟测试 (Smoke Test)
运行所有P0优先级测试，确保核心功能正常：
```powershell
python -m pytest tests/integration -k "P0" --tb=short
```

### 阶段2: 完整回归测试
运行所有测试用例，全面验证系统功能：
```powershell
python tests/integration/run_tests.py
```

### 阶段3: 性能压力测试
在高并发场景下验证系统稳定性：
```powershell
python tests/integration/test_performance.py --concurrent=10 --duration=60
```

## ✅ 验收标准

### 功能验收标准
- [ ] 所有P0测试用例通过 (100%)
- [ ] P1测试用例通过率 ≥ 90%
- [ ] 无严重安全漏洞
- [ ] 性能指标达标

### 代码质量标准
- [ ] 测试代码覆盖率 ≥ 80%
- [ ] 无测试代码缺陷
- [ ] 测试文档完整
- [ ] 测试数据可复用

### 交付物验收
- [ ] 测试用例设计文档
- [ ] 测试执行报告
- [ ] 缺陷跟踪记录
- [ ] 性能测试报告
- [ ] 安全测试报告

## 🔧 故障排查指南

### 常见问题

#### 1. Redis连接超时
**现象**: 上传任务状态一直Pending
**解决**: 
```powershell
# 检查Redis服务状态
docker-compose ps
# 重启Redis服务
docker-compose restart redis
```

#### 2. 向量数据库异常
**现象**: 搜索结果为空
**解决**:
```powershell
# 检查ChromaDB状态
python -c "import chromadb; client = chromadb.Client(); print(client.heartbeat())"
```

#### 3. LLM服务不可用
**现象**: 问答接口500错误
**解决**:
```powershell
# 检查API密钥配置
echo $env:OPENAI_API_KEY
# 验证LLM连接
python tests/integration/test_llm_connection.py
```

## 📞 支持联系

- **测试团队**: qa-team@company.com
- **开发团队**: dev-team@company.com
- **架构团队**: arch-team@company.com

---

**文档版本**: v2.0  
**最后更新**: 2024年  
**维护团队**: QA架构组