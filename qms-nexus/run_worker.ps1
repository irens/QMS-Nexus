# Worker 启动脚本（带自动重启）
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host "Starting QMS-Nexus Worker..." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow

while ($true) {
    try {
        python run_worker.py
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -eq 0) {
            Write-Host "Worker exited normally" -ForegroundColor Green
            break
        } else {
            Write-Host "Worker crashed with exit code $exitCode, restarting in 3 seconds..." -ForegroundColor Red
            Start-Sleep -Seconds 3
        }
    } catch {
        Write-Host "Worker error: $_" -ForegroundColor Red
        Write-Host "Restarting in 3 seconds..." -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
}
