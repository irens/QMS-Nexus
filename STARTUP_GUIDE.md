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
- Python 3.8+
- 依赖包：`pip install -r qms-nexus/requirements.txt`

### 前端
- Node.js 20+
- 依赖包：`cd qms-nexus-frontend && npm install`

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
