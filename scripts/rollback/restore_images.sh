#!/usr/bin/env bash
set -euo pipefail

DEPLOYMENT="${1:-yosai-dashboard}"
NAMESPACE="${2:-default}"

echo "Rolling back deployment $DEPLOYMENT in namespace $NAMESPACE to previous revision"
kubectl rollout undo deployment "$DEPLOYMENT" -n "$NAMESPACE"
