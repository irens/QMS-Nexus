# QMS-Nexus PowerShell配置文件
# 用于确保Trae在Windows环境下正确使用PowerShell命令

# 设置执行策略
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# 设置控制台编码
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$PSDefaultParameterValues['*:Encoding'] = 'UTF8'

# Git环境变量优化
$env:GIT_REDIRECT_STDERR = "2>&1"
$env:PAGER = "cat"
$env:LESS = "-F -X"

# 自定义函数用于Trae环境
function Invoke-TraeGitCommand {
    param(
        [string]$Command,
        [string]$WorkingDirectory = "d:\myproject"
    )
    
    Set-Location $WorkingDirectory
    
    # 根据命令类型添加适当的参数
    switch -regex ($Command) {
        "^git log" { 
            # 为git log添加--no-pager避免分页问题
            $Command = $Command + " --no-pager"
        }
        "^git commit -F" {
            # 确保提交信息文件存在
            $filePath = ($Command -split "-F")[1].Trim()
            if (-not (Test-Path $filePath)) {
                Write-Error "提交信息文件不存在: $filePath"
                return
            }
        }
    }
    
    Invoke-Expression $Command
}

# 设置Trae专用别名
Set-Alias -Name "trae-git" -Value Invoke-TraeGitCommand

# 项目专用函数
function Show-TraeProjectStatus {
    cd "d:\myproject\qms-nexus"
    Write-Host "=== QMS-Nexus 项目状态 ===" -ForegroundColor Green
    git status --short
    Write-Host "`n=== 最近提交记录 ===" -ForegroundColor Green
    git --no-pager log --oneline -n 3
}

function Invoke-TraeSafeCommit {
    param(
        [string]$MessageFile,
        [string]$ProjectPath = "d:\myproject\qms-nexus"
    )
    
    Set-Location $ProjectPath
    
    Write-Host "正在检查项目状态..." -ForegroundColor Yellow
    $status = git status --porcelain
    if (-not $status) {
        Write-Host "没有需要提交的变更" -ForegroundColor Green
        return
    }
    
    Write-Host "正在添加文件..." -ForegroundColor Yellow
    git add -A
    
    Write-Host "正在提交..." -ForegroundColor Yellow
    git commit -F $MessageFile
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "提交成功!" -ForegroundColor Green
        git --no-pager log --oneline -n 1
    } else {
        Write-Host "提交失败，请检查错误信息" -ForegroundColor Red
    }
}

# 导出函数
Export-ModuleMember -Function Invoke-TraeGitCommand, Show-TraeProjectStatus, Invoke-TraeSafeCommit