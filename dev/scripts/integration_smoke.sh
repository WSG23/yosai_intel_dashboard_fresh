#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# wait for services to be ready
"$SCRIPT_DIR/wait_for_services.sh" http://localhost:8000/health

# basic health check
curl -sf http://localhost:8000/health > /dev/null

# representative endpoint
curl -sf http://localhost:8000/openapi.json > /dev/null

echo "Integration smoke test passed"
