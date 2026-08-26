#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/frontend"
echo "======================================================================"
echo "Starting SentinelGraph Frontend..."
echo "Local App URL: http://localhost:3000"
echo "======================================================================"
npm run dev
