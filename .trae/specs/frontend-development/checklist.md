## 交付清单（一次性完成）

1. `Dockerfile` - 多阶段构建，Python 3.10-slim，含 MinerU 依赖与 redis/arq
2. `docker-compose.yml` - app / redis / worker 三服务，共享网络，挂载 tmp\_uploads
3. `.dockerignore` - 排除 .git/__pycache__/tmp\_uploads 等
4. `scripts/docker-build.ps1` & `docker-build.sh` - 一键构建镜像
5. `docs/docker.md` - 使用说明（启动、日志、测试命令）

## 验证目标

* `docker compose up --build` 后 Redis 自动启动

* worker 消费任务，状态由 Pending→Completed

* `docker compose run --rm app pytest` 全量测试通过

