# 阶段一完成记录（Task 1.1–1.7）

## ✅ 交付成果
| Task | 内容 | 状态 | 备注 |
|---|---|---|---|
| 1.1 | 初始化仓库 & 目录骨架 | ✅ | GitHub 已推送，目录符合规范 |
| 1.2 | requirements.txt 带哈希锁定 | ✅ | 已存在，可直接 `pip install -r` |
| 1.3 | .env.example & config.yaml 模板 | ✅ | 模板可渲染，支持多环境 |
| 1.4 | core/models.py 基础 Pydantic 模型 | ✅ | Chunk/SearchResult/EmbeddingConfig 等 |
| 1.5 | core/vectordb.py ChromaDB 连接池 | ✅ | 异步增删改查 + 来源标注，单测通过 |
| 1.6 | core/llm.py OpenAI-API 兼容层 | ✅ | 支持热切换 base_url/key，流式/非流式，单测通过 |
| 1.7 | core/parser_router.py MIME 路由 | ✅ | PDF→MinerU / Excel→Unstructured，单测通过 |

## ✅ 单元测试覆盖
- `tests/unit/test_vectordb_new.py`　写入→检索→删除 ✅
- `tests/unit/test_llm_simple.py`　流式/非流式/健康检查 ✅
- `tests/unit/test_parser_router_new.py`　MIME 路由 ✅

## ✅ 技术债清零
- ChromaDB 空 list 元数据兼容已修复
- AsyncMock 协程问题已修复

## 下一阶段入口
阶段二 Task 2.1：FastAPI 健康检查 `/health` → 2.8 完成即可进入 Alpha 阶段。