@echo off
title SentinelGraph - 1-Click All-in-One Launcher
cd /d "%~dp0"

echo ======================================================================
echo          SentinelGraph Multi-Agent Financial Crime Platform
echo ======================================================================
echo.
echo [1/3] Launching FastAPI Backend on http://localhost:8000 ...
start "SentinelGraph Backend" cmd /k "run_backend.bat"

echo [2/3] Launching React Frontend on http://localhost:3000 ...
start "SentinelGraph Frontend" cmd /k "run_frontend.bat"

echo [3/3] Opening browser in 3 seconds...
timeout /t 3 /nobreak >nul
start http://localhost:3000

echo.
echo ======================================================================
echo SentinelGraph is now running!
echo - Web Dashboard: http://localhost:3000
echo - Swagger API:   http://localhost:8000/docs
echo ======================================================================
echo You can close this window now. Backend and Frontend will keep running.
timeout /t 5 >nul
