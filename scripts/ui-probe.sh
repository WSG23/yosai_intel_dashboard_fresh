#!/usr/bin/env bash
set -euo pipefail
PORT=${PORT:-${UI_PORT:-5175}}
API="http://localhost:8000"
UI="http://localhost:$PORT"
TOKEN=${TOKEN:-dev-token}

echo "UI: $UI"
echo -n "API health: "; curl -sS "$API/healthz"; echo
echo -n "Proxy summary: "; curl -sS -H "Authorization: Bearer $TOKEN" "$UI/api/analytics/summary"; echo
echo -n "Proxy login: "; curl -sS -H 'content-type: application/json' -d '{"username":"demo","password":"x"}' "$UI/api/login"; echo
