# QMS-Nexus

配置驱动、零硬编码的 QMS 文档 RAG 系统。

## 快速启动

```bash
# 1. 初始化
cd qms-nexus
python -m venv .venv
source .venv/bin/activate  # Windows 用 .venv\Scripts\activate
pip install -r requirements.txt

# 2. 配置
cp config/.env.example config/.env
# 编辑 config/.env 与 config/config.yaml

# 3. 运行
uvicorn api.main:app --reload
```

## 文档
见 `docs/api.md`