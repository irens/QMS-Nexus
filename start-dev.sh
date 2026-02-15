#!/bin/bash

echo "========================================"
echo "QMS-Nexus 开发环境启动脚本"
echo "========================================"
echo ""

echo "[信息] 正在启动后端API服务..."
gnome-terminal --title="QMS-Nexus Backend" -- bash -c "cd ~/myproject/qms-nexus && source ./start-backend.sh; exec bash" &

sleep 5

echo "[信息] 正在启动前端开发服务器..."
gnome-terminal --title="QMS-Nexus Frontend" -- bash -c "cd ~/myproject/qms-nexus-frontend && source ./start-frontend.sh; exec bash" &

echo ""
echo "========================================"
echo "启动完成！"
echo "========================================"
echo ""
echo "请等待几秒钟让服务完全启动..."
echo ""
echo "访问地址："
echo "  前端开发服务器: http://localhost:5173"
echo "  系统首页: http://localhost:5173/system"
echo "  后端API: http://localhost:8000"
echo ""
echo "按 Ctrl+C 关闭此脚本（服务将继续在后台运行）"

# 保持脚本运行
wait
