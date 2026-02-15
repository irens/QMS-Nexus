#!/bin/bash

echo "[前端] 检查Node.js版本..."
node --version

echo "[前端] 检查依赖..."
if [ ! -d "node_modules" ]; then
    echo "[前端] 正在安装依赖..."
    npm install
fi

echo "[前端] 启动 Vite 开发服务器..."
npm run dev
