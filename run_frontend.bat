@echo off
title SentinelGraph Frontend (React + Vite)
setlocal

cd /d "%~dp0"
if exist "frontend" cd /d "%~dp0frontend"
if exist "C:\Program Files\nodejs" set "PATH=C:\Program Files\nodejs;%PATH%"

echo ======================================================================
echo Starting SentinelGraph Frontend on http://localhost:3000 ...
echo ======================================================================

if not exist "node_modules" (
    echo [Initial Setup] Installing frontend packages... Please wait ~15s.
    where npm >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        call npm install
    ) else (
        call "C:\Program Files\nodejs\npm.cmd" install
    )
)

where npm >nul 2>nul
if %ERRORLEVEL% equ 0 (
    npm run dev
) else (
    if exist "C:\Program Files\nodejs\npm.cmd" (
        "C:\Program Files\nodejs\npm.cmd" run dev
    ) else (
        echo [ERROR] Node.js / npm not found! Please install Node.js from https://nodejs.org
        pause
    )
)
pause
