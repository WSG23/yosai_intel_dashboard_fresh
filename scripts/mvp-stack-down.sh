#!/usr/bin/env bash
set -euo pipefail
pkill -f "vite" 2>/dev/null || true
docker compose -f compose.dev.yml down -v || true
echo "Stopped UI and API."
