#!/usr/bin/env bash
set -euo pipefail
PORT="${UI_PORT:-5173}"
for p in "$PORT" 5173 5174 5175 5176; do
  if curl -fsS "http://localhost:$p" >/dev/null; then PORT="$p"; break; fi
done
echo "UI: http://localhost:$PORT/"
echo -n "API health: "; curl -sS http://localhost:8000/healthz; echo
echo -n "Proxy summary: "; curl -sS "http://localhost:$PORT/api/analytics/summary"; echo
echo -n "Proxy login: "; curl -sS "http://localhost:$PORT/api/login" \
  -X POST -H 'content-type: application/json' -d '{"username":"demo","password":"x"}'; echo
