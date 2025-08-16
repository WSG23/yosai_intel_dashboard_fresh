#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

docker compose -f compose.dev.yml up -d --build api

i=0
until curl -sf http://localhost:8000/healthz >/dev/null 2>&1; do
  i=$((i+1)); [ $i -ge 60 ] && { echo "API not healthy"; exit 1; }
  sleep 1
done

cd "$ROOT/mvp-ui"
npm install >/dev/null 2>&1 || true

pkill -f "vite" 2>/dev/null || true
PORT=5173
lsof -nP -iTCP:$PORT -sTCP:LISTEN >/dev/null 2>&1 && PORT=5175
nohup npm run dev -- --host --port "$PORT" >/tmp/mvp_ui.log 2>&1 &
sleep 2

echo -n "API: " && curl -sS http://localhost:8000/healthz; echo
echo -n "UI proxy /api/analytics/summary: " && curl -sS "http://localhost:$PORT/api/analytics/summary"; echo
echo -n "UI proxy /api/login: " && curl -sS "http://localhost:$PORT/api/login" -X POST -H 'content-type: application/json' -d '{"username":"demo","password":"x"}'; echo
echo "UI: http://localhost:$PORT/"
