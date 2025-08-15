#!/usr/bin/env bash
set -euo pipefail
UI_PORT="${UI_PORT:-$(docker compose -f compose.dev.yml port ui 5173 | awk -F: 'NR==1{print $2; exit}')}"

echo -n "API: " && curl -sS http://localhost:8000/healthz; echo
echo -n "UI:  http://localhost:${UI_PORT}/ - " && (curl -sS http://localhost:${UI_PORT} >/dev/null && echo up || echo down)
echo -n "Proxy summary: " && curl -sS http://localhost:${UI_PORT}/api/analytics/summary; echo
echo -n "Proxy login: " && curl -sS http://localhost:${UI_PORT}/api/login -X POST -H 'content-type: application/json' -d '{"username":"demo","password":"x"}'; echo
