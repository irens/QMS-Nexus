# PowerShell脚本：QMS-Nexus安全Git提交流程
# 专为Windows环境优化，避免交互问题

param(
    [string]$ProjectPath = "d:\myproject\qms-nexus",
    [string]$CommitMessageFile = "COMMIT_MSG_PHASE3_FINAL.txt",
    [switch]$ShowHelp
)

if ($ShowHelp) {
    Write-Host @"
QMS-Nexus安全Git提交脚本

使用方法:
    .\safe-git-commit.ps1 [-ProjectPath <路径>] [-CommitMessageFile <文件>]

参数说明:
    -ProjectPath        项目路径 (默认: d:\myproject\qms-nexus)
    -CommitMessageFile  提交信息文件 (默认: COMMIT_MSG_PHASE3_FINAL.txt)
    -ShowHelp          显示帮助信息

示例:
    .\safe-git-commit.ps1
    .\safe-git-commit.ps1 -ProjectPath "C:\myproject" -CommitMessageFile "my_commit.txt"
"@
    exit 0
}

# 设置错误处理
$ErrorActionPreference = "Stop"

# 设置控制台编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'UTF8'

# 设置Git环境变量避免交互问题
$env:GIT_REDIRECT_STDERR = "2>&1"
$env:PAGER = "cat"
$env:LESS = "-F -X"

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-ErrorLog {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Test-GitCommand {
    param([string]$Command)
    try {
        $result = Invoke-Expression $Command 2>&1
        return $true, $result
    }
    catch {
        return $false, $_.Exception.Message
    }
}

try {
    Write-Info "开始执行QMS-Nexus安全Git提交流程..."
    Write-Info "项目路径: $ProjectPath"
    Write-Info "提交信息文件: $CommitMessageFile"
    Write-Host ""

    # 检查项目路径
    if (-not (Test-Path $ProjectPath)) {
        Write-ErrorLog "项目路径不存在: $ProjectPath"
        exit 1
    }

    # 切换到项目目录
    Write-Info "STEP 1: 切换到项目目录"
    Set-Location $ProjectPath
    Write-Success "已切换到: $(Get-Location)"
    Write-Host ""

    # 检查Git状态
    Write-Info "STEP 2: 检查Git状态"
    $success, $result = Test-GitCommand "git status --porcelain"
    if (-not $success) {
        Write-ErrorLog "Git状态检查失败: $result"
        exit 1
    }
    
    if ([string]::IsNullOrEmpty($result)) {
        Write-Warning "没有需要提交的变更"
        exit 0
    }
    
    Write-Info "发现以下变更:"
    Write-Host $result
    Write-Host ""

    # 检查提交信息文件
    $commitMessagePath = Join-Path $ProjectPath $CommitMessageFile
    if (-not (Test-Path $commitMessagePath)) {
        Write-ErrorLog "提交信息文件不存在: $commitMessagePath"
        exit 1
    }
    Write-Success "提交信息文件已找到: $commitMessagePath"
    Write-Host ""

    # 添加文件
    Write-Info "STEP 3: 添加所有变更文件"
    $success, $result = Test-GitCommand "git add -A"
    if (-not $success) {
        Write-ErrorLog "文件添加失败: $result"
        exit 1
    }
    Write-Success "所有变更文件已添加到暂存区"
    Write-Host ""

    # 执行提交
    Write-Info "STEP 4: 执行提交"
    $success, $result = Test-GitCommand "git commit -F `"$commitMessagePath`""
    if (-not $success) {
        Write-ErrorLog "提交失败: $result"
        exit 1
    }
    Write-Success "提交成功完成"
    Write-Host ""

    # 显示提交结果
    Write-Info "STEP 5: 显示提交结果"
    $success, $result = Test-GitCommand "git --no-pager log --oneline -n 1"
    if ($success) {
        Write-Info "最新提交记录:"
        Write-Host $result -ForegroundColor Green
    }
    Write-Host ""

    # 显示统计信息
    Write-Info "STEP 6: 提交统计信息"
    $success, $result = Test-GitCommand "git show --stat HEAD --no-pager"
    if ($success) {
        Write-Info "本次提交统计:"
        Write-Host $result
    }
    Write-Host ""

    # 获取提交哈希
    Write-Info "STEP 7: 获取提交哈希"
    $success, $commitHash = Test-GitCommand "git rev-parse HEAD"
    if ($success) {
        Write-Success "提交哈希: $commitHash"
    }

    Write-Host ""
    Write-Success "🎯 QMS-Nexus安全Git提交流程完成！"
    Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

} catch {
    Write-ErrorLog "发生错误: $($_.Exception.Message)"
    Write-ErrorLog "提交流程中断"
    exit 1
}

exit 0