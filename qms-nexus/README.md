# QMS-Nexus

配置驱动、零硬编码的 QMS 文档 RAG 系统。

## 快速启动

### 环境要求
- Python 3.10+
- Node.js 16+
- Docker（用于运行 Redis）

### 依赖版本要求

#### 后端依赖
- fastapi>=0.109.0
- uvicorn[standard]>=0.27.0
- pydantic>=2.5.0
- pydantic-settings>=2.0.0
- python-multipart>=0.0.9
- jinja2>=3.1.0
- pyyaml>=6.0
- python-dotenv>=1.0.0
- redis>=5.0.0
- chromadb>=1.5.0
- arq>=0.25.0
- prometheus_client>=0.24.0

#### 前端依赖
- tailwindcss@3.4.0
- postcss@8.4.38
- autoprefixer@10.4.19
- vue@^3.5.27
- element-plus@^2.13.2

### 版本兼容性说明
- **Tailwind CSS**：必须使用 3.4.0 版本，避免 PostCSS 插件冲突
- **PostCSS**：必须使用 8.4.38 版本，与 Tailwind CSS 3.4.0 兼容
- **Pydantic**：使用 v2 版本，需要安装 pydantic-settings

后续开发和部署必须严格按照以上版本要求执行，以确保系统的稳定性和兼容性。

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
# 首先进入项目目录并激活虚拟环境
cd D:\Projects\QMS-Nexus\qms-nexus
.\venv\Scripts\Activate.ps1

# 启动 Worker（后台任务处理，新终端窗口）
python run_worker.py

# 启动 API 服务（新终端窗口）
cd D:\Projects\QMS-Nexus\qms-nexus
.\venv\Scripts\Activate.ps1
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