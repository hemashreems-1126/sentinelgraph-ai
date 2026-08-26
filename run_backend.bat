@echo off
title SentinelGraph Backend (FastAPI + LangGraph)
cd /d "%~dp0backend"
echo ======================================================================
echo Starting SentinelGraph Backend on http://127.0.0.1:8000
echo Swagger API Docs: http://127.0.0.1:8000/docs
echo ======================================================================
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
pause
