@echo off
title SentinelGraph Backend (FastAPI + LangGraph)
cd /d "%~dp0backend"
echo ======================================================================
echo Starting SentinelGraph Backend on http://localhost:8000 ...
echo Swagger API Docs: http://localhost:8000/docs
echo ======================================================================

where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    python -c "import fastapi, uvicorn" >nul 2>nul
    if %ERRORLEVEL% neq 0 (
        echo [First Time Setup] Installing backend dependencies... Please wait.
        pip install -r requirements.txt
    )
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
) else (
    where py >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        py -c "import fastapi, uvicorn" >nul 2>nul
        if %ERRORLEVEL% neq 0 (
            echo [First Time Setup] Installing backend dependencies... Please wait.
            py -m pip install -r requirements.txt
        )
        py -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
    ) else (
        echo [ERROR] Python not found in PATH! Please install Python 3.10+
        pause
    )
)
