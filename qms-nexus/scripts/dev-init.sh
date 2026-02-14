#!/usr/bin/env bash
set -e
echo "🚀 初始化开发环境"
python -m venv .venv
source .venv/bin/activate  # Win 下自动切换 Scripts/activate
pip install -r requirements.txt
cp config/.env.example config/.env
echo "✅ 完成！请编辑 config/.env 后，执行: uvicorn api.main:app --reload"