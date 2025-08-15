#!/usr/bin/env bash
set -euo pipefail
UI_PORT="${UI_PORT:-}"
if [ -z "${UI_PORT}" ]; then
  for p in 5173 5174 5175 5176 5177 5178 5179 5180; do
    if ! lsof -i tcp:$p >/dev/null 2>&1; then UI_PORT=$p; break; fi
  done
fi
export UI_PORT
docker compose -f compose.dev.yml up -d --build
for i in $(seq 1 60); do curl -sf http://localhost:8000/healthz && break || sleep 1; done
for i in $(seq 1 60); do curl -sf http://localhost:$UI_PORT && break || sleep 1; done
echo -n "Proxy summary: "; curl -sS http://localhost:$UI_PORT/api/analytics/summary; echo
echo -n "Proxy login: "; curl -sS http://localhost:$UI_PORT/api/login -X POST -H 'content-type: application/json' -d '{"username":"demo","password":"x"}'; echo
echo "UI: http://localhost:$UI_PORT/"
