@echo off
title SentinelGraph - 1-Click All-in-One Launcher
setlocal

cd /d "%~dp0"
set "ROOT_DIR=%~dp0"

echo ======================================================================
echo          SentinelGraph Multi-Agent Financial Crime Platform
echo ======================================================================
echo.

:: Check frontend dependencies on fresh GitHub clone / download
if not exist "%ROOT_DIR%frontend\node_modules" (
    echo [Fresh Clone Setup] Installing frontend packages... (One-time, ~20s)
    if exist "C:\Program Files\nodejs" set "PATH=C:\Program Files\nodejs;%PATH%"
    cd /d "%ROOT_DIR%frontend"
    where npm >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        call npm install
    ) else (
        call "C:\Program Files\nodejs\npm.cmd" install
    )
    cd /d "%ROOT_DIR%"
)

echo [1/3] Launching FastAPI Backend on http://localhost:8000 ...
start "SentinelGraph Backend" /D "%ROOT_DIR%backend" cmd /k "%ROOT_DIR%run_backend.bat"

echo Waiting for Backend services to initialize...
timeout /t 4 /nobreak >nul

echo [2/3] Launching React Frontend on http://localhost:3000 ...
start "SentinelGraph Frontend" /D "%ROOT_DIR%frontend" cmd /k "%ROOT_DIR%run_frontend.bat"

echo Waiting for Frontend dev server...
timeout /t 3 /nobreak >nul

echo [3/3] Opening browser at http://localhost:3000 ...
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
