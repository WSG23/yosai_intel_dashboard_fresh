#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
pkill -f "uvicorn mvp_api:app" 2>/dev/null || true
nohup python -m uvicorn mvp_api:app --host 0.0.0.0 --port 8000 --reload >/tmp/mvp_api.log 2>&1 &
cd mvp-ui
npm install >/dev/null
pkill -f "vite" 2>/dev/null || true
nohup npm run dev -- --host --port 5173 --strictPort >/tmp/mvp_ui.log 2>&1 &
sleep 1
echo "API:  $(curl -sS http://localhost:8000/healthz || true)"
echo "UI:   http://localhost:5173/"
