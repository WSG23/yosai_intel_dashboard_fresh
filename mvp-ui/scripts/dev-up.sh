#!/usr/bin/env bash
set -euo pipefail

# Start API if not running
if ! pgrep -f "uvicorn mvp_api:app" >/dev/null; then
  nohup python -m uvicorn mvp_api:app --host 0.0.0.0 --port 8000 --reload >/tmp/mvp_api.log 2>&1 &
  echo "API starting on :8000"
fi

# Start UI if not running
if ! pgrep -f "vite" >/dev/null; then
  (cd mvp-ui && nohup npm run dev >/tmp/mvp_ui.log 2>&1 &)
  echo "UI starting on :5173"
fi

sleep 2
echo -n "Health: " && curl -sS http://localhost:8000/healthz || true
echo
echo "UI: http://localhost:5173/"
