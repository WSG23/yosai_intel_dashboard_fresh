#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="${1:-yosai-dashboard}"
NAMESPACE="${2:-default}"

CURRENT_COLOR=$(kubectl get service "$SERVICE_NAME" -n "$NAMESPACE" -o jsonpath='{.spec.selector.color}')
if [[ "$CURRENT_COLOR" == "green" ]]; then
  NEW_COLOR="blue"
else
  NEW_COLOR="green"
fi

echo "Switching $SERVICE_NAME selector to color=$NEW_COLOR in namespace $NAMESPACE"
kubectl patch service "$SERVICE_NAME" -n "$NAMESPACE" -p "{\"spec\":{\"selector\":{\"app\":\"yosai-dashboard\",\"color\":\"$NEW_COLOR\"}}}"
