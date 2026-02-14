# Docker 化使用说明

## 一键启动
Windows PowerShell：
```powershell
powershell -File scripts\docker-build.ps1
```

macOS / Linux：
```bash
chmod +x scripts/docker-build.sh
./scripts/docker-build.sh
```

服务启动后：
- FastAPI 文档：http://localhost:8000/docs
- 上传接口：POST /upload
- 状态查询：GET /upload/status/{task_id}
- 语义检索：GET /search?q=关键词

## 常用命令
```bash
# 查看实时日志
docker compose logs -f

# 仅重启 worker（更新解析逻辑后）
docker compose restart worker

# 运行全部测试
docker compose run --rm app pytest

# 停止并清理
docker compose down -v
```

## 目录挂载
- `./tmp_uploads` → 容器内 `/app/tmp_uploads`，上传文件落盘即持久化。