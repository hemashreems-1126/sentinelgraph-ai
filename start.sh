#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "======================================================================"
echo "         SentinelGraph Multi-Agent Financial Crime Platform"
echo "======================================================================"
echo ""
echo "[1/3] Starting FastAPI Backend on http://localhost:8000..."
./run_backend.sh &
BACKEND_PID=$!

echo "[2/3] Starting React Frontend on http://localhost:3000..."
./run_frontend.sh &
FRONTEND_PID=$!

echo "[3/3] Opening browser..."
sleep 3
if which xdg-open > /dev/null 2>&1; then
  xdg-open http://localhost:3000
elif which open > /dev/null 2>&1; then
  open http://localhost:3000
fi

echo "SentinelGraph is running. Press Ctrl+C to stop all services."
wait $BACKEND_PID $FRONTEND_PID
