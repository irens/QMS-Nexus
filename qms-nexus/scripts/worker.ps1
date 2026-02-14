# Windows 一键启动 arq worker
# 用法：powershell -File scripts\worker.ps1

Write-Host "启动 arq worker..." -ForegroundColor Green
python scripts\worker.py