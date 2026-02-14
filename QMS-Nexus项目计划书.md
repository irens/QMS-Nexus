# QMS-Nexus 分阶段开发计划

## 阶段一：基础环境与核心引擎（0 → 单元测试通过）
| Task | 内容 | 交付物 | 验收标准 | 工时 |
|---|---|---|---|---|
| 1.1 | 初始化 Git 仓库 & 目录骨架 | 目录结构、.gitignore、README.md | `tree -L 2` 符合方案 | 0.2 h |
| 1.2 | 写入 requirements.txt 并锁定哈希 | 带哈希的锁定文件 | `pip install -r requirements.txt` 无报错 | 0.2 h |
| 1.3 | 创建 .env.example & config.yaml 模板 | 模板文件可渲染 | `python -m core.config` 能打印合并后配置 | 0.3 h |
| 1.4 | 实现 core/models.py 基础 Pydantic 模型 | CompanyConfig / Chunk / Document | 全部字段通过 pytest 快速测试 | 0.5 h |
| 1.5 | 封装 core/vectordb.py ChromaDB 连接池 | 异步增删改查 + 持久化 | 单测：写入→检索→删除 通过 | 1 h |
| 1.6 | 封装 core/llm.py OpenAI-API 兼容层 | 支持 base_url / api_key 热切换 | 单测：流式 / 非流式 正常返回 | 1 h |
| 1.7 | 实现 core/parser_router.py 通用路由 | 根据 MIME 返回适配器实例 | 单测：PDF→MinerU / Excel→Unstructured | 0.5 h |

## 阶段二：MVP 界面与解析流（可上传→解析→检索→返回标签）
| Task | 内容 | 交付物 | 验收标准 | 工时 |
|---|---|---|---|---|
| 2.1 | 编写 api/main.py FastAPI 入口 | 健康检查 /health | `curl localhost:8000/health` 200 | 0.3 h |
| 2.2 | 实现 api/routes/upload.py 上传接口 | 异步任务 ID 即刻返回 | 上传 10 MB PDF 不阻塞 | 0.5 h |
| 2.3 | 实现 services/document_service.py 解析编排 | 调用 parser_router + 写向量库 | 单测：端到端解析通过 | 1 h |
| 2.4 | 实现 api/routes/search.py 检索接口 | 支持 ?q=&filter_tags= | 返回结果含 tags 数组 | 0.5 h |
| 2.5 | 实现 api/routes/tags.py 动态标签 CRUD | 增删改查标签池 | Postman 测试通过 | 0.5 h |
| 2.6 | 集成 services/prompt_service.py 模板渲染 | Jinja2 渲染系统提示词 | 单测：变量替换正确 | 0.5 h |
| 2.7 | 提供 scripts/dev-init.sh 一键初始化 | 自动建 venv & 装包 | Windows/Mac/Linux 均可跑 | 0.3 h |
| 2.8 | 撰写 tests/integration/test_upload_search.py | 上传→检索完整链路 | CI 通过 | 1 h |

## 阶段三：Alpha 功能增强（可商用试用）
| Task | 内容 | 交付物 | 验收标准 | 工时 |
|---|---|---|---|---|
| 3.1 | 接入 Redis + arq 异步队列 | 后台 Worker 可横向扩展 | 上传大文件后台稳定 | 1.5 h |
| 3.2 | 实现任务状态回调 /tasks/{task_id} | Pending/Processing/Completed | 前端可轮询进度条 | 1 h |
| 3.3 | 增加日志中间件 core/logger.py | 统一 JSON 日志格式 | 每条日志含 user/action/cost | 0.5 h |
| 3.4 | 限流 & 异常统一处理 api/dependencies.py | 429/500 规范返回 | Postman 验证 | 0.5 h |
| 3.5 | 实现 scripts/package.py 一键换皮 | 输入三参数输出 zip | 解压后改公司名即可启动 | 0.5 h |
| 3.6 | 撰写 docs/api.md 接口文档 | FastAPI 自动生成 | 可在线访问 /docs | 0.3 h |

## 阶段四：Beta 商业化打包（交付给外部客户）
| Task | 内容 | 交付物 | 验收标准 | 工时 |
|---|---|---|---|---|
| 4.1 | 编写 docker/Dockerfile 多阶段构建 | 最终镜像 < 80 MB | `docker run` 一键启动 | 1 h |
| 4.2 | 提供 docker-compose.yml 生产版 | 内置 Chroma 持久卷 | `docker-compose up -d` 可用 | 0.5 h |
| 4.3 | 实现 scripts/benchmark.py 压测脚本 | 并发上传/检索 100 线程 | 95th 延迟 < 2 s | 1 h |
| 4.4 | 撰写 README.md 商业化版 | 含 Logo、换皮教程、FAQ | Markdown 美观 | 1 h |
| 4.5 | 提供 LICENSE 与合规声明 | MIT 或商业授权 | 法务可接受 | 0.2 h |
| 4.6 | 最终回归测试 & Tag 1.0.0 | Git tag + Release | GitHub Release 可下载 | 0.5 h |

---
总计 21 个 Task，阶段内可并行，阶段间严格串行。