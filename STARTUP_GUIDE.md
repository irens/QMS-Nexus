# QMS-Nexus 快速启动指南

## 一键启动（推荐）

### Windows 系统

双击运行：
```
start-dev.bat
```

这会同时启动后端API和前端开发服务器，并自动打开两个命令行窗口。

### Linux/macOS 系统

```bash
chmod +x start-dev.sh
./start-dev.sh
```

## 手动启动

### 方式1：分别启动

**启动后端API：**
```bash
# Windows
start-backend.bat

# Linux/macOS
cd qms-nexus
./start-backend.sh
```

**启动前端：**
```bash
# Windows
start-frontend.bat

# Linux/macOS
cd qms-nexus-frontend
./start-frontend.sh
```

### 方式2：命令行启动

**后端API：**
```bash
cd qms-nexus
uvicorn api.main:app --reload --port 8000
```

**前端开发服务器：**
```bash
cd qms-nexus-frontend
npm run dev
```

## 访问地址

服务启动后，访问以下地址：

- **系统首页**：http://localhost:5173/system
- **Dashboard**：http://localhost:5173/system/dashboard
- **文档管理**：http://localhost:5173/system/documents
- **智能问答**：http://localhost:5173/system/chat
- **文件上传**：http://localhost:5173/system/upload

## 开发环境要求

### 后端
- Python 3.10+
- 核心依赖版本：
  - fastapi>=0.109.0
  - uvicorn[standard]>=0.27.0
  - pydantic>=2.5.0
  - pydantic-settings>=2.0.0
  - redis>=5.0.0
  - chromadb>=1.5.0
  - arq>=0.25.0
  - prometheus_client>=0.24.0
- 安装依赖：`pip install -r qms-nexus/requirements.txt`

### 前端
- Node.js 16+
- 核心依赖版本：
  - tailwindcss@3.4.0
  - postcss@8.4.38
  - autoprefixer@10.4.19
  - vue@^3.5.27
  - element-plus@^2.13.2
- 安装依赖：`cd qms-nexus-frontend && npm install`

### 版本兼容性说明
- Tailwind CSS 必须使用 3.4.0 版本，避免 PostCSS 插件冲突
- PostCSS 必须使用 8.4.38 版本，与 Tailwind CSS 3.4.0 兼容
- Pydantic 使用 v2 版本，需要安装 pydantic-settings
- 后续开发和部署必须严格按照以上版本要求执行

## 常见问题

### 端口占用
如果8000或5173端口被占用，请修改脚本中的端口号。

### 虚拟环境
建议在后端使用Python虚拟环境：
```bash
cd qms-nexus
python -m venv venv
```

### 首次运行
首次运行前请确保安装依赖：
```bash
# 后端
cd qms-nexus
pip install -r requirements.txt

# 前端
cd qms-nexus-frontend
npm install
```

## 部署

生产环境部署请使用：
```bash
cd qms-nexus-frontend
deploy.bat  # Windows
./deploy.sh  # Linux/macOS
```

更多部署信息请查看 DEPLOYMENT_CHECKLIST.md
