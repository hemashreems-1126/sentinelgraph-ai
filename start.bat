@echo off
title SentinelGraph - 1-Click All-in-One Launcher
setlocal EnableDelayedExpansion

cd /d "%~dp0"

echo ======================================================================
echo          SentinelGraph Multi-Agent Financial Crime Platform
echo ======================================================================
echo.

:: Ensure frontend dependencies exist
if not exist "%~dp0frontend\node_modules" (
    echo [Initial Clone Setup] Installing frontend packages... (One-time, ~20s)
    if exist "C:\Program Files\nodejs" set "PATH=C:\Program Files\nodejs;!PATH!"
    cd /d "%~dp0frontend"
    where npm >nul 2>nul
    if !ERRORLEVEL! equ 0 (
        call npm install
    ) else (
        call "C:\Program Files\nodejs\npm.cmd" install
    )
    cd /d "%~dp0"
)

echo [1/3] Launching FastAPI Backend on http://localhost:8000 ...
start "SentinelGraph Backend" /D "%~dp0" run_backend.bat

echo Waiting 3 seconds for Backend to warm up...
timeout /t 3 /nobreak >nul

echo [2/3] Launching React Frontend on http://localhost:3000 ...
start "SentinelGraph Frontend" /D "%~dp0" run_frontend.bat

echo Waiting 2 seconds for Frontend dev server...
timeout /t 2 /nobreak >nul

echo [3/3] Opening browser at http://localhost:3000 ...
start http://localhost:3000

echo.
echo ======================================================================
echo SentinelGraph is RUNNING!
echo - Web Dashboard: http://localhost:3000
echo - Swagger API:   http://localhost:8000/docs
echo ======================================================================
echo Please keep the Backend and Frontend command windows open in background.
echo.
pause
