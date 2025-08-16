#!/usr/bin/env bash
set -euo pipefail
CFILE=compose.dev.yml
CID=$(docker compose -f "$CFILE" ps -q api || true)
echo "API container: ${CID:-<none>}"
if [ -n "${CID:-}" ]; then
  echo "--- logs: api (last 120) ---"
  docker logs --tail 120 "$CID" || true
  echo "--- health detail ---"
  docker inspect "$CID" --format '{{json .State.Health}}' | python -m json.tool 2>/dev/null || docker inspect "$CID" --format '{{json .State.Health}}' || true
fi
echo "--- probe host:8000/healthz ---"
if curl -sf http://localhost:8000/healthz >/dev/null; then echo "OK"; else echo "FAIL"; fi
if [ -n "${CID:-}" ]; then
  echo "--- probe inside container:8000/healthz ---"
  docker exec "$CID" sh -lc 'curl -sS http://localhost:8000/healthz || true'
fi
