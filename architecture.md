# QMS-Nexus 系统架构设计文档

## 版本信息
- **版本**: v1.0.0
- **创建日期**: 2026-02-23
- **状态**: 设计中（冻结，不再变更）

---

## 1. 项目概述

### 1.1 产品定位
QMS-Nexus 是一款面向医疗器械质量管理体系的智能问答系统，支持多格式文档上传、解析、向量化存储和精准问答。

### 1.2 目标用户
- 医疗器械企业质量管理人员
- 合规审核人员
- 内网多用户同时使用（≥20人并发）

### 1.3 核心功能
1. **文档管理**: PDF/Word/Excel/PPT 上传、解析、分块、向量化
2. **智能问答**: 基于 RAG 的精准问答，带来源标注
3. **反馈闭环**: 赞/踩反馈、人工修正、修正库优先检索
4. **多租户**: 多知识库隔离、API Key 管理、调用统计
5. **系统管理**: 日志查看、备份恢复、系统监控

---

## 2. 技术架构

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                         前端层 (Frontend)                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Vue 3     │  │  Element    │  │      Axios/Pinia        │  │
│  │  (TypeScript)│  │   Plus      │  │                         │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTP/REST
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API 网关层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   FastAPI   │  │  CORS/限流   │  │    认证中间件            │  │
│  │   (Python)  │  │             │  │   (API Key/IP白名单)     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│   业务路由层   │    │   核心服务层   │    │   数据存储层   │
├───────────────┤    ├───────────────┤    ├───────────────┤
│ /upload       │    │ DocumentService│   │ SQLite        │
│ /search       │    │ RAGService    │    │  (关系数据)    │
│ /ask          │    │ LLMClient     │    │               │
│ /corrections  │    │ ParserRouter  │    │ ChromaDB      │
│ /knowledge-bases│  │ AuthService   │    │  (向量数据)    │
│ /api-keys     │    │ KBService     │    │               │
│ /system       │    │ CorrectionSvc │    │ Redis         │
│               │    │ StatsService  │    │  (任务队列)    │
└───────────────┘    └───────────────┘    └───────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      异步任务队列 (Worker)                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │    arq      │  │  Document   │  │      VectorDB           │  │
│  │   (Redis)   │  │   Parser    │  │      Upsert             │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      外部服务集成                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  OpenAI API │  │  Azure API  │  │      Ollama             │  │
│  │  (云端LLM)   │  │  (云端LLM)   │  │   (本地LLM)             │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 技术栈

| 层级 | 技术选型 | 版本 |
|------|---------|------|
| 前端 | Vue 3 + TypeScript + Element Plus | ^3.4.0 |
| 后端 | FastAPI + Python | ^3.12 |
| 数据库 | SQLite (关系型) | 3.x |
| 向量库 | ChromaDB | ^0.6.0 |
| 任务队列 | Redis + arq | Redis 7.x |
| 文档解析 | PyMuPDF + python-docx + openpyxl + python-pptx | - |
| LLM 集成 | OpenAI API / Azure / Ollama | - |

---

## 3. 数据模型设计

### 3.1 数据库架构 (SQLite)

统一使用单数据库文件: `./data/qms_nexus.db`

#### 3.1.1 文档表 (documents)
```sql
CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    filename TEXT NOT NULL,
    file_type TEXT,
    file_size INTEGER,
    upload_time TIMESTAMP,
    status TEXT DEFAULT 'Pending', -- Pending/Processing/Completed/Failed
    tags TEXT, -- JSON 数组
    metadata TEXT, -- JSON 对象
    chunks_count INTEGER,
    parse_time REAL,
    error_message TEXT,
    kb_id TEXT DEFAULT 'default', -- 所属知识库
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.1.2 标签表 (tags)
```sql
CREATE TABLE tags (
    id TEXT PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    color TEXT DEFAULT '#409EFF',
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.1.3 知识库表 (knowledge_bases)
```sql
CREATE TABLE knowledge_bases (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    collection_name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    metadata TEXT,
    document_count INTEGER DEFAULT 0
);
```

#### 3.1.4 修正库表 (corrections)
```sql
CREATE TABLE corrections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    question TEXT NOT NULL UNIQUE,
    correct_answer TEXT NOT NULL,
    original_answer TEXT,
    source_doc TEXT,
    page_number INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    metadata TEXT
);
```

#### 3.1.5 问答日志表 (chat_logs)
```sql
CREATE TABLE chat_logs (
    id TEXT PRIMARY KEY,
    user_id TEXT,
    kb_id TEXT DEFAULT 'default',
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    sources TEXT, -- JSON 数组
    is_corrected BOOLEAN DEFAULT FALSE,
    correction_id INTEGER,
    response_time_ms INTEGER,
    model_used TEXT,
    tokens_used INTEGER,
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (correction_id) REFERENCES corrections(id)
);
```

#### 3.1.6 反馈表 (feedbacks)
```sql
CREATE TABLE feedbacks (
    id TEXT PRIMARY KEY,
    chat_log_id TEXT NOT NULL,
    rating TEXT NOT NULL CHECK(rating IN ('thumbs_up', 'thumbs_down')),
    comment TEXT,
    user_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (chat_log_id) REFERENCES chat_logs(id)
);
```

#### 3.1.7 API Key 表 (api_keys)
```sql
CREATE TABLE api_keys (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    key_hash TEXT NOT NULL UNIQUE,
    key_preview TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    request_count INTEGER DEFAULT 0,
    rate_limit INTEGER DEFAULT 1000
);
```

#### 3.1.8 IP 白名单表 (ip_whitelist)
```sql
CREATE TABLE ip_whitelist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT NOT NULL UNIQUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);
```

#### 3.1.9 系统日志表 (system_logs)
```sql
CREATE TABLE system_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    level TEXT NOT NULL, -- DEBUG/INFO/WARNING/ERROR/CRITICAL
    module TEXT,
    message TEXT NOT NULL,
    user_id TEXT,
    request_id TEXT,
    ip_address TEXT,
    metadata TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3.1.10 API 调用统计表 (api_call_stats)
```sql
CREATE TABLE api_call_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_key_id TEXT,
    endpoint TEXT,
    method TEXT,
    status_code INTEGER,
    response_time_ms INTEGER,
    created_at DATE
);
```

#### 3.1.11 用户表 (users)
```sql
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT,
    role TEXT DEFAULT 'user' CHECK(role IN ('admin', 'user', 'guest')),
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP
);
```

#### 3.1.12 认证配置表 (auth_config)
```sql
CREATE TABLE auth_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
-- 默认配置
INSERT INTO auth_config (key, value) VALUES
('auth_enabled', '0'),
('whitelist_enabled', '0');
```

### 3.2 向量库架构 (ChromaDB)

- **集合命名**: `kb_{知识库ID}`，默认 `qms_docs`
- **文档结构**:
  ```json
  {
    "id": "chunk_uuid",
    "text": "文本内容",
    "metadata": {
      "filename": "文档名",
      "file_type": "pdf",
      "page": 1,
      "total_pages": 10,
      "doc_id": "文档ID",
      "kb_id": "知识库ID"
    }
  }
  ```

### 3.3 Redis 数据结构

- **任务队列**: `arq:queue:qms_nexus_queue`
- **任务状态**: `qms:task:{task_id}` (Hash)

---

## 4. API 设计

### 4.1 接口清单

| 模块 | 接口 | 方法 | 说明 |
|------|------|------|------|
| 健康检查 | /health | GET | 服务状态检查 |
| 上传 | /upload | POST | 文件上传（异步） |
| 上传 | /upload/status/{task_id} | GET | 查询上传状态 |
| 文档 | /documents | GET | 文档列表 |
| 文档 | /documents/{id} | GET | 文档详情 |
| 文档 | /documents/{id} | DELETE | 删除文档 |
| 文档 | /documents/{id}/preview | GET | 文档预览 |
| 文档 | /documents/{id}/download | GET | 下载文档 |
| 搜索 | /search | POST | 语义搜索 |
| 问答 | /ask | POST | 智能问答 |
| 问答 | /ask-with-correction | POST | 带修正的问答 |
| 标签 | /tags | GET/POST | 标签列表/创建 |
| 标签 | /tags/{id} | PUT/DELETE | 标签更新/删除 |
| 知识库 | /knowledge-bases | GET/POST | 知识库列表/创建 |
| 知识库 | /knowledge-bases/{id} | GET/PUT/DELETE | 知识库详情/更新/删除 |
| 修正库 | /corrections | GET/POST | 修正记录列表/创建 |
| 修正库 | /corrections/{id} | GET/PUT/DELETE | 修正记录详情/更新/删除 |
| 反馈 | /feedback | POST | 提交赞/踩反馈 |
| 认证 | /api-keys | GET/POST | API Key 列表/创建 |
| 认证 | /api-keys/{id}/revoke | POST | 吊销 API Key |
| 认证 | /ip-whitelist | GET/POST | IP 白名单列表/添加 |
| 认证 | /ip-whitelist/{id} | DELETE | 移除 IP 白名单 |
| 系统 | /system/status | GET | 系统状态 |
| 系统 | /system/logs | GET | 系统日志 |
| 系统 | /system/backup | POST | 创建备份 |
| 系统 | /system/backups | GET | 备份列表 |
| 系统 | /system/restore/{id} | POST | 恢复备份 |
| 统计 | /statistics/dashboard | GET | 仪表盘数据 |
| 统计 | /statistics/api-calls | GET | API 调用统计 |

### 4.2 认证方式

1. **API Key**: Header `Authorization: Bearer sk-xxxx` 或 `Authorization: sk-xxxx`
2. **IP 白名单**: 客户端 IP 在白名单内
3. **JWT Token**: (可选) 用户登录后获取

---

## 5. 核心服务设计

### 5.1 服务清单

| 服务 | 文件 | 职责 |
|------|------|------|
| DatabaseManager | core/database.py | 数据库连接池管理 |
| DocumentService | services/document_service.py | 文档上传、解析编排 |
| RAGService | services/rag_service.py | RAG 检索、问答生成 |
| LLMClient | core/llm.py | LLM API 调用封装 |
| ParserRouter | core/parser_router.py | 文档解析路由 |
| AuthService | core/auth.py | API Key/IP 白名单管理 |
| KBService | core/knowledge_base.py | 多知识库管理 |
| CorrectionService | core/correction_service.py | 修正库管理 |
| StatsService | core/stats_service.py | 统计服务 |
| LogStore | core/log_store.py | 系统日志管理 |
| TaskStore | core/task_store.py | 任务状态管理 |

### 5.2 异步任务

| 任务 | 函数名 | 说明 |
|------|--------|------|
| 文档解析 | parse_doc_task | 解析文档并写入向量库 |

---

## 6. 配置管理

### 6.1 配置文件

- **环境变量**: `.env`
- **配置文件**: `config/config.yaml`
- **配置类**: `core/config.py`

### 6.2 配置项

```python
class Settings(BaseSettings):
    # 基础配置
    APP_NAME: str = "QMS-Nexus"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/qms_nexus.db"
    
    # 向量库配置
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    
    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"
    ARQ_QUEUE_NAME: str = "qms_nexus_queue"
    
    # LLM 配置
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_TIMEOUT: int = 60
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_RETENTION_DAYS: int = 30
    LOG_MAX_SIZE_MB: int = 10
    
    # 安全配置
    JWT_SECRET: str = "your-secret-key"
    JWT_EXPIRE_HOURS: int = 24
```

---

## 7. 目录结构

```
qms-nexus/
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI 入口
│   ├── dependencies.py      # 依赖注入
│   └── routes/
│       ├── __init__.py
│       ├── auth.py          # 认证管理
│       ├── correction.py    # 修正库
│       ├── documents.py     # 文档管理
│       ├── health.py        # 健康检查
│       ├── knowledge_base.py # 知识库
│       ├── search.py        # 搜索
│       ├── system.py        # 系统管理
│       ├── tags.py          # 标签管理
│       └── upload.py        # 文件上传
├── config/
│   └── config.yaml          # 配置文件
├── core/
│   ├── __init__.py
│   ├── auth.py              # 认证服务
│   ├── cache.py             # 缓存
│   ├── config.py            # 配置管理
│   ├── correction_service.py # 修正服务
│   ├── database.py          # 数据库管理
│   ├── knowledge_base.py    # 知识库服务
│   ├── llm.py               # LLM 客户端
│   ├── log_store.py         # 日志存储
│   ├── logger.py            # 日志配置
│   ├── metrics.py           # 监控指标
│   ├── models.py            # Pydantic 模型
│   ├── parser_router.py     # 解析器路由
│   ├── rag_service.py       # RAG 服务
│   ├── stats_service.py     # 统计服务
│   ├── task_store.py        # 任务存储
│   ├── vectordb.py          # 向量库客户端
│   └── worker.py            # Worker 配置
├── data/                    # 数据目录
│   ├── backups/             # 备份文件
│   └── logs/                # 日志文件
├── docs/                    # 文档
│   ├── api.md               # API 文档
│   └── phase*.md            # 阶段文档
├── parsers/                 # 解析器
│   └── parser.py            # 解析器基类
├── scripts/                 # 脚本
│   ├── dev-init.sh          # 开发初始化
│   ├── worker.py            # Worker 启动
│   └── backup.py            # 备份脚本
├── services/                # 业务服务
│   ├── document_service.py  # 文档服务
│   └── prompt_service.py    # 提示词服务
├── tests/                   # 测试
│   ├── unit/                # 单元测试
│   └── integration/         # 集成测试
├── .env                     # 环境变量
├── .env.example             # 环境变量模板
├── requirements.txt         # 依赖
└── README.md                # 项目说明
```

---

## 8. 部署架构

### 8.1 开发环境

```bash
# 1. 启动后端
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 2. 启动 Worker
python scripts/worker.py

# 3. 启动前端
cd qms-nexus-frontend && npm run dev
```

### 8.2 生产环境

```bash
# Docker 部署
docker-compose up -d
```

### 8.3 组件清单

| 组件 | 开发 | 生产 |
|------|------|------|
| FastAPI | 1 实例 | 2+ 实例 (负载均衡) |
| Worker | 1 实例 | 2+ 实例 |
| Redis | 单机 | 主从/哨兵 |
| SQLite | 单文件 | 备份策略 |
| ChromaDB | 本地持久化 | 持久化卷 |

---

## 9. 安全设计

### 9.1 认证授权
- API Key 认证
- IP 白名单
- (可选) JWT 用户认证

### 9.2 数据安全
- 密码 bcrypt 加密
- API Key SHA256 哈希存储
- 敏感配置环境变量管理

### 9.3 访问控制
- 基于角色的权限控制 (RBAC)
- 接口限流

---

## 10. 监控与日志

### 10.1 日志
- 应用日志: `./logs/app/`
- 系统日志: `./logs/system/`
- 错误日志: `./logs/error/`

### 10.2 监控
- Prometheus 指标
- 健康检查接口
- 系统状态 API

---

## 11. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0.0 | 2026-02-23 | 初始架构设计，冻结 |

---

## 12. 附录

### 12.1 参考文档
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [ChromaDB 文档](https://docs.trychroma.com/)
- [Vue 3 文档](https://vuejs.org/)

### 12.2 命名规范
- 数据库表: 小写下划线 (snake_case)
- Python 类: 大驼峰 (PascalCase)
- Python 函数/变量: 小写下划线 (snake_case)
- API 路径: 小写中划线 (kebab-case)
