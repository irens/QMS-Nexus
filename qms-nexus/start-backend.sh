#!/bin/bash

echo "[后端] 检查Python虚拟环境..."
if [ -d "venv" ]; then
    echo "[后端] 激活虚拟环境..."
    source venv/bin/activate
else
    echo "[后端] 未找到虚拟环境，使用系统Python..."
fi

echo "[后端] 检查依赖包..."
if ! python -c "import uvicorn" > /dev/null 2>&1; then
    echo "[后端] 正在安装依赖..."
    pip install -r requirements.txt
fi

echo "[后端] 启动 Uvicorn 服务器..."
uvicorn api.main:app --reload --port 8000 --host 0.0.0.0
