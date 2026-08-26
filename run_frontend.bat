@echo off
title SentinelGraph Frontend (React + Vite)
cd /d "%~dp0frontend"
set "PATH=C:\Program Files\nodejs;%PATH%"
echo ======================================================================
echo Starting SentinelGraph Frontend on http://localhost:3000
echo ======================================================================
"C:\Program Files\nodejs\npm.cmd" run dev
pause
