# QMS-Nexus 待完成任务清单

> **版本**: v1.0.0  
> **状态**: 架构已冻结，按顺序执行  
> **说明**: 每个任务包含完整提示词，可直接发给 AI 完成

---

## 🔴 阶段一：基础设施（必须按顺序完成）

### 任务 1：数据库统一架构设计
- **优先级**: P0（阻塞性）
- **文件**: `core/database.py`(新建)
- **当前状态**: 多个独立 SQLite 文件（auth.db, corrections.db, knowledge_bases.db）
- **目标状态**: 统一使用 `./data/qms_nexus.db`
- **详细需求**:
  1. 创建 `core/database.py`，实现 DatabaseManager 单例类
  2. 使用 SQLAlchemy ORM 管理所有表
  3. 实现数据库迁移机制（版本管理）
  4. 创建所有表（12个）：documents, tags, knowledge_bases, corrections, chat_logs, feedbacks, api_keys, ip_whitelist, system_logs, api_call_stats, users, auth_config
  5. 表结构严格遵循 architecture.md 第 3.1 节
  6. 实现连接池管理
  7. 提供初始化脚本，首次启动自动建表
- **验收标准**:
  - [ ] 所有表能正常创建
  - [ ] 支持事务操作
  - [ ] 数据库文件只生成一个 `./data/qms_nexus.db`
  - [ ] 现有数据（如有）能平滑迁移

### 任务 2：配置管理优化
- **优先级**: P0
- **文件**: `core/config.py`, `.env.example`
- **当前状态**: 配置项不完整，部分硬编码
- **详细需求**:
  1. 扩展 Settings 类，添加以下配置项：
     - DATABASE_URL: SQLite 数据库路径（默认 sqlite:///./data/qms_nexus.db）
     - LOG_LEVEL: 日志级别（默认 INFO）
     - LOG_RETENTION_DAYS: 日志保留天数（默认 30）
     - LOG_MAX_SIZE_MB: 单日志文件最大大小（默认 10）
     - LLM_API_KEY: LLM 服务 API 密钥
     - LLM_BASE_URL: LLM 服务基础 URL（默认 https://api.openai.com/v1）
     - LLM_MODEL: 默认模型名称（默认 gpt-3.5-turbo）
     - LLM_TIMEOUT: 请求超时时间（默认 60 秒）
     - JWT_SECRET: JWT 密钥（用于认证）
     - JWT_EXPIRE_HOURS: Token 过期时间（默认 24）
  2. 所有配置项支持环境变量覆盖（使用 pydantic Settings）
  3. 更新 `.env.example` 模板，包含所有配置项示例
  4. 启动时验证配置完整性，缺失关键配置报错并提示
- **验收标准**:
  - [ ] 所有配置可通过 .env 文件配置
  - [ ] 缺失 LLM_API_KEY 时给出友好提示
  - [ ] 配置值正确读取并生效

### 任务 3：将标签存储从内存级迁移到数据库
- **优先级**: P0
- **文件**: `api/routes/tags.py`, `core/tag_store.py`(新建)
- **当前状态**: 使用 `tags_store: Dict[str, dict] = {}` 内存存储，重启丢失
- **详细需求**:
  1. 创建 `core/tag_store.py`，实现 TagStore 类
  2. 使用 SQLAlchemy 定义 Tag 模型（表结构见 architecture.md 3.1.2）
  3. 实现 CRUD 方法：create, get_by_id, get_by_name, list_all, update, delete
  4. 保持现有 API 接口不变（/api/v1/tags/*）
  5. 初始化时自动创建表
  6. 添加 usage_count 自动统计功能
  7. 名称唯一性约束，重复名称返回 409 错误
- **依赖**: 任务 1（数据库架构）
- **验收标准**:
  - [ ] 重启服务后标签数据不丢失
  - [ ] 所有 CRUD 操作正常
  - [ ] 标签名称唯一性约束生效
  - [ ] 与文档的关联关系正确

### 任务 4：将文档元数据存储从内存级迁移到数据库
- **优先级**: P0
- **文件**: `api/routes/documents.py`, `core/document_store.py`(新建)
- **当前状态**: 使用 `documents_store: dict = {}` 内存存储
- **详细需求**:
  1. 创建 `core/document_store.py`，实现 DocumentStore 类
  2. 使用 SQLAlchemy 定义 Document 模型（表结构见 architecture.md 3.1.1）
  3. 实现复杂查询方法：支持筛选、排序、分页、全文搜索
  4. 保持现有 API 接口不变（/api/v1/documents/*）
  5. 全文搜索使用 SQLite FTS 扩展或 LIKE 查询
  6. 支持按标签筛选（tags 字段存储 JSON 数组）
  7. 支持按文件类型、状态、时间范围筛选
- **依赖**: 任务 1（数据库架构）
- **验收标准**:
  - [ ] 重启服务后文档数据不丢失
  - [ ] 支持所有筛选、排序、分页操作
  - [ ] 全文搜索响应时间 < 500ms
  - [ ] 与 ChromaDB 的文档 ID 保持一致

---

## 🔴 阶段二：核心功能（可并行）

### 任务 5：实现系统日志功能
- **优先级**: P1
- **文件**: `core/log_store.py`(新建), `api/routes/system.py`
- **当前状态**: `get_system_logs()` 返回模拟数据
- **详细需求**:
  1. 创建 `core/log_store.py`，实现 LogStore 类
  2. 使用 `logging.handlers.TimedRotatingFileHandler` 实现文件存储
  3. 日志目录: `./logs/system/`，按天分割，保留 30 天
  4. 单文件最大 10MB，超过自动轮转
  5. 支持级别: DEBUG/INFO/WARNING/ERROR/CRITICAL
  6. 日志格式: `时间|级别|模块|消息|用户ID|请求ID`
  7. 同时写入数据库表 system_logs（便于查询）
  8. 实现 API: GET /api/v1/system/logs?level=INFO&module=upload&startTime=xxx&endTime=xxx&page=1&pageSize=20
  9. 支持按级别、模块、时间范围筛选，支持模糊搜索消息内容
- **依赖**: 任务 1（数据库架构）
- **验收标准**:
  - [ ] 调用 API 能返回真实日志数据
  - [ ] 日志文件按规则正确轮转
  - [ ] 数据库和文件双写成功
  - [ ] 日志级别筛选正常

### 任务 6：实现问答日志记录功能
- **优先级**: P1
- **文件**: `core/chat_logger.py`(新建), `api/routes/ask.py`(修改)
- **当前状态**: 未实现，无问答记录
- **需求来源**: US-Alpha-04
- **详细需求**:
  1. 创建 `core/chat_logger.py`，实现 ChatLogger 类
  2. 表结构 chat_logs（见 architecture.md 3.1.5）
  3. 在 /ask 和 /ask-with-correction 接口中自动记录
  4. 记录字段：用户ID、知识库ID、问题、答案、来源、是否修正、模型、token数、响应时间、IP地址
  5. 实现 API: GET /api/v1/chat/logs?page=1&pageSize=20&userId=xxx&startTime=xxx&endTime=xxx
  6. 支持按用户、知识库、时间范围筛选
  7. 支持模糊搜索问题内容
- **依赖**: 任务 1（数据库架构）
- **验收标准**:
  - [ ] 每次问答自动记录到数据库
  - [ ] 查询接口返回正确数据
  - [ ] 响应时间统计准确

### 任务 7：实现用户反馈（赞/踩）功能
- **优先级**: P1
- **文件**: `api/routes/feedback.py`(新建), `core/feedback_store.py`(新建)
- **当前状态**: 未实现
- **需求来源**: US-Alpha-02
- **详细需求**:
  1. 创建 `core/feedback_store.py`，实现 FeedbackStore 类
  2. 表结构 feedbacks（见 architecture.md 3.1.6）
  3. API: POST /api/v1/feedback
     - 请求体: {chatLogId: string, rating: 'thumbs_up' | 'thumbs_down', comment?: string}
  4. API: GET /api/v1/feedback/stats
     - 返回各问答的赞/踩统计
  5. 一个用户对同一问答只能反馈一次（可选：更新机制）
  6. 前端在问答结果旁显示赞/踩按钮
- **依赖**: 任务 6（问答日志）
- **验收标准**:
  - [ ] 能正常提交赞/踩反馈
  - [ ] 统计接口返回正确数据
  - [ ] 重复反馈处理正确

### 任务 8：实现人工修正答案功能
- **优先级**: P1
- **文件**: `api/routes/correction.py`(新建), `core/correction_service.py`(重构), `services/rag_service.py`(修改)
- **当前状态**: `correction_service.py` 存在但需检查是否符合需求
- **需求来源**: US-Alpha-03, US-Alpha-06
- **详细需求**:
  1. 检查并完善 `core/correction_service.py`，确保表结构符合 architecture.md 3.1.4
  2. API: POST /api/v1/corrections
     - 请求体: {question: string, wrongAnswer?: string, correctAnswer: string, sourceChatLogId?: string}
  3. API: GET /api/v1/corrections?page=1&pageSize=20&search=xxx
  4. API: PUT /api/v1/corrections/{id}
  5. API: DELETE /api/v1/corrections/{id}
  6. 修改 RAGService.answer() 方法:
     - 优先查询修正库（使用问题相似度匹配）
     - 如果匹配度 > 阈值(如0.9)，直接返回修正答案
     - 标注"人工修正答案"并显示修正者信息
  7. 前端支持提交修正、查看修正库
- **依赖**: 任务 1（数据库架构）
- **验收标准**:
  - [ ] 修正库 CRUD 操作正常
  - [ ] RAG 检索时优先返回修正答案
  - [ ] 修正答案正确标注来源
  - [ ] 相似度匹配阈值可配置

---

## 🟡 阶段三：集成与优化（可并行）

### 任务 9：集成真实的 LLM 服务调用
- **优先级**: P2
- **文件**: `core/llm.py`(检查并完善), `README.md`(更新)
- **当前状态**: 已实现基础 HTTP 客户端，需验证和完善
- **详细需求**:
  1. 检查现有 LLMClient 实现:
     - 支持 OpenAI API 格式
     - 支持流式输出
     - 支持非流式输出
  2. 新增功能:
     - 支持配置多个模型（gpt-3.5-turbo, gpt-4, claude 等）
     - 支持模型自动降级（gpt-4 失败时尝试 gpt-3.5）
     - 添加请求重试机制（最多3次）
     - 添加超时处理
     - 记录 token 使用量到 chat_logs
  3. 在 .env 中添加配置示例（见 architecture.md 6.2）
  4. 更新 README.md，添加 LLM 配置说明章节
- **验收标准**:
  - [ ] 配置正确后能正常调用 LLM API
  - [ ] 流式输出正常
  - [ ] Token 使用量正确记录
  - [ ] 失败时自动降级

### 任务 10：实现系统服务重启功能
- **优先级**: P2
- **文件**: `api/routes/system.py`
- **当前状态**: `restart_system()` 返回模拟数据
- **详细需求**:
  1. 实现 POST /api/v1/system/restart/{service}
  2. 支持重启的服务: backend, worker, redis
  3. 实现方式:
     - Windows: 使用 subprocess 调用 PowerShell 脚本
     - Linux: 使用 subprocess 调用 systemctl 或 supervisorctl
  4. 安全验证:
     - 需要管理员权限（后续集成认证后）
     - 记录重启操作到系统日志
  5. 返回重启状态（异步操作，立即返回"重启中"）
- **验收标准**:
  - [ ] 调用接口后服务能正常重启
  - [ ] 重启操作记录到日志
  - [ ] 不支持的平台返回友好错误

### 任务 11：实现系统备份/恢复功能
- **优先级**: P2
- **文件**: `api/routes/system.py`, `core/backup_manager.py`(新建)
- **当前状态**: `backup_system()`, `restore_system()` 返回模拟数据
- **详细需求**:
  1. 创建 `core/backup_manager.py`，实现 BackupManager 类
  2. 备份内容:
     - SQLite 数据库文件
     - ChromaDB 数据目录
     - Redis 数据（使用 redis-cli bgsave 后复制 rdb 文件）
     - 配置文件（.env, config.yaml）
  3. 备份格式: zip 压缩包
  4. 备份文件命名: `qms_backup_YYYYMMDD_HHMMSS.zip`
  5. 备份存储目录: `./backups/`
  6. API: POST /api/v1/system/backup
     - 可选参数: autoDeleteDays（自动删除N天前的备份，默认30）
  7. API: GET /api/v1/system/backups?page=1&pageSize=20
  8. API: POST /api/v1/system/restore/{backupId}
     - 恢复前自动创建当前状态备份
     - 恢复后需要重启服务（提示用户）
  9. API: DELETE /api/v1/system/backups/{backupId}
  10. 支持定时自动备份（使用 APScheduler）
- **依赖**: 任务 1（数据库架构）
- **验收标准**:
  - [ ] 备份文件包含所有必要数据
  - [ ] 恢复后数据完整
  - [ ] 自动删除旧备份正常

---

## 🟢 阶段四：增强功能（可延后）

### 任务 12：实现 API Key 管理功能
- **优先级**: P3
- **文件**: `api/routes/auth.py`(已存在，检查完善), `core/auth.py`(已存在，检查完善)
- **当前状态**: 已实现基础功能，需检查是否完整
- **需求来源**: US-Beta-01
- **详细需求**:
  1. 检查现有 `core/auth.py` 和 `api/routes/auth.py`
  2. 确保表结构符合 architecture.md 3.1.7
  3. 确保功能完整:
     - API Key 生成（32位随机字符串，sk-前缀）
     - API Key 吊销/删除
     - IP 白名单管理
     - 认证开关配置
  4. 添加 rate_limit 字段支持
  5. 中间件验证 API Key 和 IP 白名单
  6. 前端管理界面（如需要）
- **依赖**: 任务 1（数据库架构）
- **验收标准**:
  - [ ] API Key 生成和验证正常
  - [ ] 无效 Key 返回 403
  - [ ] IP 白名单生效
  - [ ] 认证开关可配置

### 任务 13：实现 API 调用统计功能
- **优先级**: P3
- **文件**: `api/routes/statistics.py`(新建), `core/stats_service.py`(新建)
- **当前状态**: 未实现
- **需求来源**: US-Beta-02
- **详细需求**:
  1. 创建 `core/stats_service.py`，实现 StatsService 类
  2. 表结构 api_call_stats（见 architecture.md 3.1.10）
  3. 中间件自动记录每次 API 调用
  4. API: GET /api/v1/statistics/api-calls?apiKeyId=xxx&startDate=xxx&endDate=xxx&groupBy=day
     - 返回按天/周/月统计的调用次数
  5. API: GET /api/v1/statistics/api-calls/export?format=excel
     - 导出 Excel 报表
     - 使用 openpyxl 生成
  6. API: GET /api/v1/statistics/dashboard
     - 返回仪表盘数据（总调用次数、成功率、平均响应时间等）
- **依赖**: 任务 12（API Key管理）
- **验收标准**:
  - [ ] 统计数据准确
  - [ ] Excel 导出文件可正常打开
  - [ ] 仪表盘数据实时更新

### 任务 14：添加用户认证和权限管理
- **优先级**: P3
- **文件**: `core/auth.py`, `api/routes/auth.py`
- **当前状态**: 基础框架存在，使用 API Key 认证
- **详细需求**:
  1. 使用 JWT 实现用户认证（补充现有 API Key 认证）
  2. 用户表 users（见 architecture.md 3.1.11）
  3. API: POST /api/v1/auth/register
  4. API: POST /api/v1/auth/login
     - 返回 JWT access_token 和 refresh_token
  5. API: POST /api/v1/auth/refresh
  6. API: POST /api/v1/auth/logout
  7. API: GET /api/v1/auth/me
  8. 权限控制:
     - 使用依赖注入保护路由
     - @require_auth 装饰器
     - @require_admin 装饰器
  9. 密码安全:
     - 使用 bcrypt 加密
     - 密码强度验证
- **依赖**: 任务 1（数据库架构）
- **验收标准**:
  - [ ] 登录后获得有效 JWT
  - [ ] 受保护路由需要认证
  - [ ] 权限控制生效
  - [ ] 密码加密存储

### 任务 15：实现文档预览功能
- **优先级**: P3
- **文件**: `api/routes/documents.py`
- **当前状态**: `preview_document()` 返回模拟内容
- **详细需求**:
  1. 修改 `preview_document()` 函数
  2. API: GET /api/v1/documents/{id}/preview?page=1&pageSize=500
  3. 实现方式:
     - 从 ChromaDB 查询该文档的所有 chunks
     - 按页码排序后返回
     - 每页返回指定字符数（默认500字符）
  4. 返回格式:
     ```json
     {
       "documentId": "xxx",
       "filename": "xxx.pdf",
       "totalPages": 10,
       "currentPage": 1,
       "content": "文本内容...",
       "hasMore": true
     }
     ```
- **验收标准**:
  - [ ] 能正确返回文档内容
  - [ ] 分页正常
  - [ ] 前端预览界面正常显示

---

## 📋 测试覆盖要求

每个任务完成后必须补充以下测试：

### 单元测试
- 放在 `tests/unit/` 目录
- 命名规范: `test_{模块名}.py`
- 覆盖率要求: > 80%
- 必须包含:
  * 正常流程测试
  * 异常处理测试
  * 边界条件测试

### 集成测试
- 放在 `tests/integration/` 目录
- 命名规范: `test_{功能名}_integration.py`
- 测试内容:
  * API 端到端测试
  * 数据库操作测试
  * 第三方服务 Mock 测试

### API 契约测试
- 验证请求/响应格式符合 `docs/api-contract.md`
- 验证状态码和错误处理

---

## 🔧 开发规范

### 代码风格
- 遵循 PEP 8 规范
- 使用类型注解
- 函数和类必须添加 docstring

### 提交规范
- 提交信息格式: `[模块] 简短描述`
- 示例: `[database] 添加 SQLAlchemy 模型定义`

### 文档更新
- 修改 API 后更新 `docs/api.md`
- 新增配置后更新 `.env.example` 和 `README.md`

---

## ✅ 已完成任务

| 任务 | 说明 | 完成日期 |
|------|------|----------|
| 文档解析 | 使用 PyMuPDF/python-docx/openpyxl/python-pptx 实现真实解析 | 2026-02-23 |
| 任务状态存储 | 从内存迁移到 Redis | 2026-02-23 |
| 前端上传状态修复 | 修复上传状态显示"等待中"问题 | 2026-02-23 |

---

## 📚 参考文档

- [architecture.md](./architecture.md) - 系统架构设计
- [QMS-Nexus产品需求.md](./QMS-Nexus产品需求.md) - 产品需求文档
- [docs/api-contract.md](./qms-nexus/docs/api-contract.md) - API 契约文档
