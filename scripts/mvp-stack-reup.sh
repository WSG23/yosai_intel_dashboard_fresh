#!/usr/bin/env bash
set -euo pipefail
docker compose -f compose.dev.yml up -d --build
UI_PORT="${UI_PORT:-$(docker compose -f compose.dev.yml port ui 5173 | awk -F: 'NR==1{print $2; exit}')}"

for i in $(seq 1 60); do curl -sf http://localhost:8000/healthz && break || sleep 1; done
for i in $(seq 1 60); do curl -sf http://localhost:${UI_PORT} && break || sleep 1; done

echo -n "Proxy summary: " && curl -sS http://localhost:${UI_PORT}/api/analytics/summary; echo
echo -n "Proxy login: " && curl -sS http://localhost:${UI_PORT}/api/login -X POST -H 'content-type: application/json' -d '{"username":"demo","password":"x"}'; echo
echo "UI: http://localhost:${UI_PORT}/"
