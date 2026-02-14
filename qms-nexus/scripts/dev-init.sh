#!/usr/bin/env bash
# QMS-Nexus 开发环境一键初始化脚本
# 支持 Linux / macOS / Git-Bash

set -e

echo "🚀 QMS-Nexus 开发环境初始化开始"

# 1. 检测 Python 版本
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
required="3.10"
if ! printf '%s\n' "$required" "$python_version" | sort -V -C; then
  echo "❌ 需要 Python $required+，当前 $python_version"
  exit 1
fi

# 2. 创建/激活 venv
if [ ! -d "venv" ]; then
  echo "📦 创建 venv..."
  python3 -m venv venv
fi
source venv/bin/activate

# 3. 升级 pip
python -m pip install --upgrade pip

# 4. 安装依赖
pip install -r requirements.txt

# 5. 生成 .env（若不存在）
if [ ! -f ".env" ]; then
  cp .env.example .env
  echo "✅ 已生成 .env，请按需修改"
fi

# 6. 创建 tmp 目录
mkdir -p tmp_uploads

# 7. 运行单元测试快速验证
python -m pytest tests/unit -v --tb=short

echo "✅ 初始化完成！激活命令：source venv/bin/activate"