# 缓存使用说明

## 功能
- 问答结果缓存 5 分钟 TTL，减少重复 LLM 调用
- 缓存未命中时自动走完整 RAG 流程并回填

## 环境变量
`CACHE_URL=redis://redis:6379/1`（已在 docker-compose.yml 配置）

## 日志
命中时输出：缓存命中
未命中时输出：完成问答 并写入缓存

## 测试
```bash
docker compose run --rm app pytest tests/unit/test_cache.py -v
```