@echo off
chcp 65001 >nul

:: QMS-Nexus 前端部署脚本（Windows版本）
:: 适用于 Nginx 部署方式

echo ========================================
echo QMS-Nexus 前端部署脚本
echo ========================================
echo.

:: 配置变量
set NGINX_CONF_DIR=C:\nginx\conf\conf.d
set NGINX_HTML_DIR=C:\nginx\html\qms-nexus
set BACKUP_DIR=C:\backup\qms-nexus-%date:~-4,4%%date:~-7,2%%date:~-10,2%-%time:~0,2%%time:~3,2%%time:~6,2%

:: 检查必要命令
where npm >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] npm 命令未找到，请先安装Node.js
    pause
    exit /b 1
)

where nginx >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] nginx 命令未找到，请先安装Nginx
    pause
    exit /b 1
)

echo [信息] 开始部署 QMS-Nexus 前端...
echo.

:: 步骤1：创建备份
echo [信息] 创建备份...
if exist "%NGINX_HTML_DIR%" (
    mkdir "%BACKUP_DIR%"
    xcopy /E /I /Y "%NGINX_HTML_DIR%\*" "%BACKUP_DIR%\"
    echo [信息] 备份已创建: %BACKUP_DIR%
) else (
    echo [警告] Nginx HTML目录不存在，跳过备份
)
echo.

:: 步骤2：构建应用
echo [信息] 构建前端应用...

:: 检查node_modules是否存在
if not exist "node_modules" (
    echo [信息] 安装依赖...
    npm ci --only=production
)

:: 执行构建
call npm run build

if %errorlevel% neq 0 (
    echo [错误] 构建失败
    pause
    exit /b 1
)
echo [信息] 构建成功
echo.

:: 步骤3：部署静态文件
echo [信息] 部署静态文件...

:: 创建目标目录
if not exist "%NGINX_HTML_DIR%" (
    mkdir "%NGINX_HTML_DIR%"
)

:: 复制文件
xcopy /E /I /Y "dist\*" "%NGINX_HTML_DIR%\"

echo [信息] 静态文件部署完成
echo.

:: 步骤4：配置Nginx
echo [信息] 配置Nginx...

:: 检查nginx.conf文件是否存在
if not exist "nginx.conf" (
    echo [错误] nginx.conf文件不存在，请先创建配置文件
    pause
    exit /b 1
)

:: 备份旧配置
if exist "%NGINX_CONF_DIR%\qms-nexus.conf" (
    copy /Y "%NGINX_CONF_DIR%\qms-nexus.conf" "%NGINX_CONF_DIR%\qms-nexus.conf.backup"
    echo [信息] 已备份旧Nginx配置
)

:: 复制新配置
copy /Y "nginx.conf" "%NGINX_CONF_DIR%\qms-nexus.conf"

:: 检查配置
echo [信息] 检查Nginx配置...
nginx -t

if %errorlevel% neq 0 (
    echo [错误] Nginx配置检查失败
    
    :: 回滚配置
    if exist "%NGINX_CONF_DIR%\qms-nexus.conf.backup" (
        echo [信息] 回滚配置...
        copy /Y "%NGINX_CONF_DIR%\qms-nexus.conf.backup" "%NGINX_CONF_DIR%\qms-nexus.conf"
    )
    pause
    exit /b 1
)

:: 重载Nginx
echo [信息] 重载Nginx...
nginx -s reload

echo [信息] Nginx配置已更新并重载
echo.

:: 步骤5：健康检查
echo [信息] 执行健康检查...
echo [信息] 等待Nginx启动...
timeout /t 3 /nobreak >nul

:: 检查首页
curl -f http://localhost/system >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 首页访问失败
) else (
    echo [信息] 首页访问正常
)

:: 检查dashboard
curl -f http://localhost/system/dashboard >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Dashboard访问失败
) else (
    echo [信息] Dashboard访问正常
)

echo [信息] 健康检查完成
echo.

:: 显示部署信息
echo ========================================
echo 部署完成！
echo ========================================
echo.
echo 访问地址:
echo   系统首页: http://localhost/system
echo   Dashboard: http://localhost/system/dashboard
echo   文档列表: http://localhost/system/documents
echo   智能问答: http://localhost/system/chat
echo.
echo 重要路由:
echo   旧路由 /documents - 自动重定向到 /system/documents
echo   旧路由 /chat - 自动重定向到 /system/chat
echo.
echo Nginx配置:
echo   配置文件: %NGINX_CONF_DIR%\qms-nexus.conf
echo   静态文件: %NGINX_HTML_DIR%
echo.
echo 备份目录:
echo   %BACKUP_DIR%
echo.
echo [信息] 部署成功！
echo.

pause
