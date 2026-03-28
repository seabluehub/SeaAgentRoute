@echo off
echo ========================================
echo   AI Gateway - 一键启动脚本
echo ========================================
echo.

REM 检查 .env 文件是否存在
if not exist ".env" (
    echo [警告] 未找到 .env 文件！
    echo [提示] 正在从 .env.example 复制...
    copy ".env.example" ".env"
    echo.
    echo [注意] 请编辑 .env 文件，填入真实的 API Keys！
    echo.
)

REM 检查是否已安装依赖
echo [信息] 检查 Python 依赖...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [信息] 正在安装依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败！
        pause
        exit /b 1
    )
)

echo.
echo [信息] 启动 AI Gateway...
echo.
echo 服务地址: http://localhost:8000
echo 健康检查: http://localhost:8000/health
echo.
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

REM 启动 uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause
