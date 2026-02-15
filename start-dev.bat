@echo off
echo ========================================
echo QMS-Nexus 开发环境启动脚本
echo ========================================
echo.

echo [信息] 正在启动后端API服务...
start "QMS-Nexus Backend" cmd /k "cd /d d:\myproject\qms-nexus && call :start_backend"

timeout /t 5 /nobreak >nul

echo [信息] 正在启动前端开发服务器...
start "QMS-Nexus Frontend" cmd /k "cd /d d:\myproject\qms-nexus-frontend && call :start_frontend"

echo.
echo ========================================
echo 启动完成！
echo ========================================
echo.
echo 请等待几秒钟让服务完全启动...
echo.
echo 访问地址：
echo   前端开发服务器: http://localhost:5173
echo   系统首页: http://localhost:5173/system
echo   后端API: http://localhost:8000
echo.
echo 按任意键关闭此窗口（服务将在后台继续运行）
pause >nul
exit

:start_backend
echo [后端] 检查Python虚拟环境...
if exist "venv\Scripts\activate.bat" (
    echo [后端] 激活虚拟环境...
    call venv\Scripts\activate.bat
) else (
    echo [后端] 未找到虚拟环境，使用系统Python...
)

echo [后端] 检查依赖包...
python -c "import uvicorn" >nul 2>&1
if %errorlevel% neq 0 (
    echo [后端] 正在安装依赖...
    pip install -r requirements.txt
)

echo [后端] 启动 Uvicorn 服务器...
uvicorn api.main:app --reload --port 8000 --host 0.0.0.0
goto :eof

:start_frontend
echo [前端] 检查Node.js版本...
node --version

echo [前端] 检查依赖...
if not exist "node_modules" (
    echo [前端] 正在安装依赖...
    npm install
)

echo [前端] 启动 Vite 开发服务器...
npm run dev
goto :eof
