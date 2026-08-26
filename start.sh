#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"

echo "======================================================================"
echo "         SentinelGraph Multi-Agent Financial Crime Platform"
echo "======================================================================"
echo ""

# Check frontend dependencies on fresh clone
if [ ! -d "frontend/node_modules" ]; then
    echo "[Fresh Clone Setup] Installing frontend packages..."
    cd frontend && npm install && cd ..
fi

echo "[1/3] Starting FastAPI Backend on http://localhost:8000..."
./run_backend.sh &
BACKEND_PID=$!

sleep 4

echo "[2/3] Starting React Frontend on http://localhost:3000..."
./run_frontend.sh &
FRONTEND_PID=$!

sleep 3

echo "[3/3] Opening browser..."
if which xdg-open > /dev/null 2>&1; then
  xdg-open http://localhost:3000
elif which open > /dev/null 2>&1; then
  open http://localhost:3000
fi

echo "SentinelGraph is running. Press Ctrl+C to stop all services."
wait $BACKEND_PID $FRONTEND_PID
