#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/backend"
echo "======================================================================"
echo "Starting SentinelGraph Backend..."
echo "Local API URL: http://127.0.0.1:8000"
echo "Swagger API Docs: http://127.0.0.1:8000/docs"
echo "======================================================================"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
