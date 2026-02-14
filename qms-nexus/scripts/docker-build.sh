#!/usr/bin/env bash
set -e

echo "开始构建 QMS-Nexus Docker 镜像..."
docker compose build --no-cache

echo "构建完成，正在启动服务..."
docker compose up -d

echo "服务已启动，访问 http://localhost:8000"
echo "查看日志：docker compose logs -f"