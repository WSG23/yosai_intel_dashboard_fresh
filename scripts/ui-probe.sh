#!/usr/bin/env bash
set -euo pipefail
PORT="${PORT:-$(docker compose -f compose.dev.yml port ui 5173 2>/dev/null | awk -F: '{print $2}' || echo 5173)}"
for i in $(seq 1 60); do
  curl -sf "http://localhost:$PORT" >/dev/null && break || sleep 1
done
echo "UI: http://localhost:$PORT/"
echo -n "API health: "; curl -sS http://localhost:8000/healthz; echo
echo -n "Proxy summary: "; curl -sS "http://localhost:$PORT/api/analytics/summary"; echo
echo -n "Proxy login: "; curl -sS "http://localhost:$PORT/api/login" -X POST -H 'content-type: application/json' -d '{"username":"demo","password":"x"}'; echo
