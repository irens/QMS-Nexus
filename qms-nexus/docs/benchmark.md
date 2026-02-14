# 性能压测说明

## 一键压测
服务启动后执行：
```bash
docker compose run --rm app python scripts/benchmark.py
```

## 输出示例
总请求：200
QPS：42.3
P95 延迟：0.123s
成功率：100%

## 调优建议
- 提高 worker 并发：增加 `worker` 容器副本数
- 降低延迟：调大 `top_k` 或减少 `chunk_size`
- 提升 QPS：启用更多 Redis 缓存命中率