# QMS-Nexus 项目启动指南

**生成时间**: 2026-02-15  
**项目路径**: d:/myproject

---

## 📋 项目结构

```
d:/myproject/
├── qms-nexus/              # 后端项目 (Python + FastAPI)
│   ├── api/                # API路由
│   ├── api/main.py         # 后端入口
│   ├── config/             # 配置文件
│   ├── docker-compose.yml  # Docker配置
│   ├── requirements.txt    # Python依赖
│   └── ...
│
└── qms-nexus-frontend/     # 前端项目 (Vue 3 + TypeScript)
    ├── src/                # 源代码
    ├── package.json        # npm配置
    └── ...
```

---

## 🚀 启动方式选择

### 方式一：手动启动（推荐开发使用）

#### 1. 启动后端 (Python)

**步骤**:

```powershell
# 1. 进入后端目录
cd d:/myproject/qms-nexus

# 2. 创建虚拟环境
python -m venv .venv

# 3. 激活虚拟环境
.venv\Scripts\activate

# 4. 安装依赖
pip install -r requirements.txt

# 5. 启动后端服务
uvicorn api.main:app --reload --port 8000 --host 0.0.0.0
```

**后端访问地址**:
- API文档: http://localhost:8000/docs
- 服务地址: http://localhost:8000

---

#### 2. 启动前端 (Vue)

**步骤**:

```powershell
# 1. 进入前端目录（新终端窗口）
cd d:/myproject/qms-nexus-frontend

# 2. 安装依赖（如果还没安装）
npm install

# 3. 启动前端开发服务器
npm run dev
```

**前端访问地址**:
- 开发服务器: http://localhost:5173
- 预览地址: http://localhost:4173 (build后)

---

### 方式二：Docker Compose 启动（推荐生产使用）

**步骤**:

```powershell
# 1. 进入后端目录
cd d:/myproject/qms-nexus

# 2. 启动所有服务（包括Redis、后端、Worker、监控）
docker-compose up -d

# 3. 查看服务状态
docker-compose ps

# 4. 查看日志
docker-compose logs -f app
```

**服务端口**:
- 后端API: http://localhost:8000
- Redis: localhost:6379
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

---

### 方式三：批处理脚本启动（一键启动）

创建 `start-all.bat` 文件:

```batch
@echo off
chcp 65001

echo ========================================
echo  QMS-Nexus 项目启动脚本
echo ========================================
echo.

:: 启动后端
echo [1/2] 正在启动后端服务...
start "QMS Backend" cmd /k "cd /d d:\myproject\qms-nexus && .venv\Scripts\activate && uvicorn api.main:app --reload --port 8000"

:: 等待2秒
timeout /t 2 /nobreak >nul

:: 启动前端
echo [2/2] 正在启动前端服务...
start "QMS Frontend" cmd /k "cd /d d:\myproject\qms-nexus-frontend && npm run dev"

echo.
echo ========================================
echo  服务启动完成！
echo ========================================
echo.
echo 后端地址: http://localhost:8000
echo 前端地址: http://localhost:5173
echo.
echo 按任意键退出...
pause >nul
```

---

## 📊 启动后访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 前端页面 | http://localhost:5173 | Vue 3开发服务器 |
| 后端API | http://localhost:8000 | FastAPI服务 |
| API文档 | http://localhost:8000/docs | Swagger UI文档 |
| ReDoc文档 | http://localhost:8000/redoc | 替代API文档 |

---

## 🔧 环境配置

### 后端环境变量

创建/编辑 `qms-nexus/config/.env`:

```env
# 基础配置
DEBUG=true
HOST=0.0.0.0
PORT=8000

# 数据库配置
DATABASE_URL=sqlite:///./qms.db

# Redis配置
REDIS_URL=redis://localhost:6379/0
CACHE_URL=redis://localhost:6379/1

# 文档解析配置
UPLOAD_DIR=./tmp_uploads
MAX_FILE_SIZE=52428800

# 日志配置
LOG_LEVEL=INFO
LOG_DIR=./logs
```

### 前端代理配置

前端 `vite.config.ts` 已配置代理:

```typescript
server: {
  port: 3000,
  proxy: {
    '/api': {
      target: 'http://localhost:8000',
      changeOrigin: true,
      rewrite: (path) => path.replace(/^\/api/, '/api/v1')
    }
  }
}
```

---

## ⚠️ 常见问题

### 1. 后端启动失败

**问题**: `ModuleNotFoundError: No module named 'xxx'`

**解决**:
```powershell
cd d:/myproject/qms-nexus
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 前端启动失败

**问题**: `Cannot find module 'xxx'`

**解决**:
```powershell
cd d:/myproject/qms-nexus-frontend
npm install
npm run dev
```

### 3. 端口被占用

**问题**: `Port 8000 is already in use`

**解决**:
```powershell
# 查看占用端口的进程
netstat -ano | findstr :8000

# 结束进程
taskkill /PID <进程ID> /F
```

### 4. CORS跨域问题

后端已配置CORS，如果仍有问题，检查:
- 后端是否正确启动
- 前端代理配置是否正确
- 浏览器缓存是否已清除

---

## 📝 启动命令速查

### 后端命令

```powershell
# 启动
uvicorn api.main:app --reload --port 8000

# 后台运行（Windows）
start /B uvicorn api.main:app --reload --port 8000

# Docker启动
docker-compose up -d

# 停止
docker-compose down
```

### 前端命令

```powershell
# 开发模式
npm run dev

# 构建
npm run build

# 预览构建结果
npm run preview

# 测试
npm run test
```

---

## 🎯 验证启动成功

### 后端验证

```powershell
# 测试API健康检查
curl http://localhost:8000/health

# 预期返回
{"status": "ok"}
```

### 前端验证

打开浏览器访问 http://localhost:5173，应该能看到:
- QMS-Nexus 登录页面
- 导航菜单
- 各功能模块入口

---

**指南生成时间**: 2026-02-15  
**适用版本**: QMS-Nexus v1.0.0
