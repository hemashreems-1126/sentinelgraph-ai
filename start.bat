@echo off
title SentinelGraph - 1-Click All-in-One Launcher
setlocal

cd /d "%~dp0"
set "ROOT_DIR=%~dp0"

echo ======================================================================
echo          SentinelGraph Multi-Agent Financial Crime Platform
echo ======================================================================
echo.
echo [1/3] Launching FastAPI Backend on http://localhost:8000 ...
start "SentinelGraph Backend" /D "%ROOT_DIR%backend" cmd /k "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [2/3] Launching React Frontend on http://localhost:3000 ...
start "SentinelGraph Frontend" /D "%ROOT_DIR%frontend" cmd /k "set PATH=C:\Program Files\nodejs;%%PATH%% && npm run dev"

echo [3/3] Waiting for servers to initialize...
timeout /t 4 /nobreak >nul

echo Opening browser at http://localhost:3000 ...
start http://localhost:3000

echo.
echo ======================================================================
echo SentinelGraph is RUNNING!
echo - Web Dashboard: http://localhost:3000
echo - Swagger API:   http://localhost:8000/docs
echo ======================================================================
echo Please keep the two black server windows open while using the app.
echo.
pause
