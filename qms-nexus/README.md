# QMS-Nexus

配置驱动、零硬编码的 QMS 文档 RAG 系统。

## 快速启动

### 环境要求
- Python 3.10+
- Node.js 16+
- Docker（用于运行 Redis）

### 启动步骤

```bash
# 1. 初始化后端
cd qms-nexus
python -m venv venv
# Windows
.\venv\Scripts\Activate.ps1
# Linux/Mac
source venv/bin/activate
pip install -r requirements.txt

# 2. 启动 Redis
# 方法1：使用 Docker
 docker run -d --name qms_redis -p 6379:6379 redis:7-alpine
# 方法2：使用 docker-compose
# docker-compose up -d redis

# 3. 启动后端服务
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# 4. 启动前端（新终端）
cd qms-nexus-frontend
npm install  # 首次运行
npm run dev
```

### 服务访问地址
- 后端服务：http://localhost:8000
- 后端API文档：http://localhost:8000/docs
- 前端服务：http://localhost:5173
- Redis：localhost:6379

## 文档
见 `docs/api.md`