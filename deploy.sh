#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "--dry-run" ]]; then
  echo "[DRY RUN] Would deploy image tag $(git rev-parse --short HEAD)"
  exit 0
fi

echo "Deploying image tag $(git rev-parse --short HEAD)"
# Placeholder for real deployment commands
