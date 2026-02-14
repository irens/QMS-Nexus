# Windows 一键构建 & 启动脚本
# 用法：powershell -File scripts\docker-build.ps1

Write-Host "开始构建 QMS-Nexus Docker 镜像..." -ForegroundColor Green

docker compose build --no-cache
if ($LASTEXITCODE -ne 0) {
    Write-Host "构建失败！" -ForegroundColor Red
    exit 1
}

Write-Host "构建完成，正在启动服务..." -ForegroundColor Green
docker compose up -d

Write-Host "服务已启动，访问 http://localhost:8000" -ForegroundColor Green
Write-Host "查看日志：docker compose logs -f" -ForegroundColor Yellow