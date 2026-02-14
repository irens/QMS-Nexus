# QMS-Nexus 开发环境一键初始化脚本（Windows PowerShell）

Write-Host "🚀 QMS-Nexus 开发环境初始化开始" -ForegroundColor Green

# 1. 检测 Python 版本
$pythonVersion = (python --version 2>&1) -replace 'Python ', ''
$required = [version]'3.10'
$current = [version]$pythonVersion
if ($current -lt $required) {
    Write-Host "❌ 需要 Python $required+，当前 $current" -ForegroundColor Red
    exit 1
}

# 2. 创建/激活 venv
if (-not (Test-Path "venv")) {
    Write-Host "📦 创建 venv..."
    python -m venv venv
}
& .\venv\Scripts\Activate.ps1

# 3. 升级 pip
python -m pip install --upgrade pip

# 4. 安装依赖
pip install -r requirements.txt

# 5. 生成 .env（若不存在）
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" -Destination ".env"
    Write-Host "✅ 已生成 .env，请按需修改" -ForegroundColor Yellow
}

# 6. 创建 tmp 目录
New-Item -ItemType Directory -Force -Path "tmp_uploads" | Out-Null

# 7. 运行单元测试快速验证
python -m pytest tests/unit -v --tb=short

Write-Host "✅ 初始化完成！激活命令：.\venv\Scripts\Activate.ps1" -ForegroundColor Green