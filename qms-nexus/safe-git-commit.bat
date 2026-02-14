@echo off
REM Windows批处理脚本：安全Git提交流程
REM 用于QMS-Nexus项目的自动化提交

setlocal enabledelayedexpansion

REM 设置项目路径
set "PROJECT_PATH=d:\myproject\qms-nexus"
set "COMMIT_MSG_FILE=COMMIT_MSG_PHASE3_FINAL.txt"

echo [INFO] 开始执行Git安全提交流程...
echo [INFO] 项目路径: %PROJECT_PATH%
echo [INFO] 提交信息文件: %COMMIT_MSG_FILE%

REM 切换到项目目录
cd /d "%PROJECT_PATH%"
if %errorlevel% neq 0 (
    echo [ERROR] 无法切换到项目目录: %PROJECT_PATH%
    exit /b 1
)

echo.
echo [STEP 1] 检查Git状态...
git status --porcelain
if %errorlevel% neq 0 (
    echo [ERROR] Git状态检查失败
    exit /b 1
)

echo.
echo [STEP 2] 添加所有变更文件...
git add -A
if %errorlevel% neq 0 (
    echo [ERROR] 文件添加失败
    exit /b 1
)
echo [SUCCESS] 文件添加完成

REM 检查提交信息文件是否存在
if not exist "%COMMIT_MSG_FILE%" (
    echo [ERROR] 提交信息文件不存在: %COMMIT_MSG_FILE%
    exit /b 1
)

echo.
echo [STEP 3] 执行提交...
git commit -F "%COMMIT_MSG_FILE%"
if %errorlevel% neq 0 (
    echo [ERROR] 提交失败
    exit /b 1
)
echo [SUCCESS] 提交成功

echo.
echo [STEP 4] 显示提交结果...
echo [INFO] 最新提交记录:
git --no-pager log --oneline -n 1

echo.
echo [STEP 5] 统计提交变更...
echo [INFO] 本次提交统计:
git show --stat HEAD --no-pager

echo.
echo [SUCCESS] Git提交流程完成!
echo [INFO] 提交哈希: 
git rev-parse HEAD

endlocal
exit /b 0