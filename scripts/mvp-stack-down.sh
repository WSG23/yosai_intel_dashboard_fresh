#!/usr/bin/env bash
set -euo pipefail
docker compose -f compose.dev.yml down -v || true
