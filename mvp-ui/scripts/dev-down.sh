#!/usr/bin/env bash
set -euo pipefail
pkill -f "uvicorn mvp_api:app" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
echo "Stopped API and UI dev servers."
