# QMS-Nexus Windows Git提交工具
# 专为Windows PowerShell环境优化

param(
    [string]$ProjectPath = "d:\myproject\qms-nexus",
    [string]$CommitMessageFile = "COMMIT_MSG_PHASE3_FINAL.txt"
)

# 设置控制台编码和环境
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PAGER = "cat"
$env:GIT_REDIRECT_STDERR = "2>&1"

function Show-Usage {
    Write-Host "QMS-Nexus Windows Git提交工具" -ForegroundColor Green
    Write-Host "使用方法: .\windows-git-commit.ps1 [-ProjectPath 路径] [-CommitMessageFile 文件]" -ForegroundColor Yellow
    Write-Host "示例: .\windows-git-commit.ps1" -ForegroundColor Cyan
}

function Test-GitCommand {
    param([string]$Command)
    try {
        $output = Invoke-Expression $Command 2>&1
        return $true, $output
    }
    catch {
        return $false, $_.Exception.Message
    }
}

# 主函数
function Main {
    Write-Host "🚀 QMS-Nexus Windows Git提交工具" -ForegroundColor Green
    Write-Host "项目路径: $ProjectPath" -ForegroundColor Cyan
    Write-Host "提交文件: $CommitMessageFile" -ForegroundColor Cyan
    Write-Host ""

    try {
        # 检查项目路径
        if (-not (Test-Path $ProjectPath)) {
            Write-Host "❌ 项目路径不存在: $ProjectPath" -ForegroundColor Red
            return 1
        }

        # 切换到项目目录
        Set-Location $ProjectPath
        Write-Host "✅ 当前目录: $(Get-Location)" -ForegroundColor Green

        # 检查Git状态
        Write-Host "📊 检查Git状态..." -ForegroundColor Yellow
        $success, $output = Test-GitCommand "git status --porcelain"
        if (-not $success) {
            Write-Host "❌ Git状态检查失败" -ForegroundColor Red
            return 1
        }

        if ([string]::IsNullOrEmpty($output)) {
            Write-Host "⚠️  没有需要提交的变更" -ForegroundColor Yellow
            return 0
        }

        Write-Host "📋 发现变更:" -ForegroundColor Cyan
        Write-Host $output

        # 检查提交信息文件
        $commitPath = Join-Path $ProjectPath $CommitMessageFile
        if (-not (Test-Path $commitPath)) {
            Write-Host "❌ 提交信息文件不存在: $commitPath" -ForegroundColor Red
            return 1
        }

        # 添加文件
        Write-Host "📥 添加文件到暂存区..." -ForegroundColor Yellow
        $success, $output = Test-GitCommand "git add -A"
        if (-not $success) {
            Write-Host "❌ 文件添加失败: $output" -ForegroundColor Red
            return 1
        }
        Write-Host "✅ 文件添加成功" -ForegroundColor Green

        # 执行提交
        Write-Host "📝 执行提交..." -ForegroundColor Yellow
        $success, $output = Test-GitCommand "git commit -F `"$commitPath`""
        if (-not $success) {
            Write-Host "❌ 提交失败: $output" -ForegroundColor Red
            return 1
        }
        Write-Host "✅ 提交成功" -ForegroundColor Green

        # 显示提交结果
        Write-Host "📈 提交结果:" -ForegroundColor Cyan
        $success, $output = Test-GitCommand "git --no-pager log --oneline -n 1"
        if ($success) {
            Write-Host $output -ForegroundColor Green
        }

        Write-Host ""
        Write-Host "🎉 Git提交完成!" -ForegroundColor Green
        return 0

    }
    catch {
        Write-Host "❌ 发生错误: $($_.Exception.Message)" -ForegroundColor Red
        return 1
    }
}

# 执行主函数
$exitCode = Main
exit $exitCode