#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "--test" ]]; then
  echo "[TEST MODE] Simulating rollback for deployment/yosai-dashboard"
  echo "kubectl rollout undo deployment/yosai-dashboard"
  echo "kubectl rollout status deployment/yosai-dashboard"
  exit 0
fi

scripts/rollback.sh "$@"
