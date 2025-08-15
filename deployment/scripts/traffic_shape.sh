#!/usr/bin/env bash
set -euo pipefail

# Toggle target environment, defaulting to staging
TARGET_ENV="${TARGET_ENV:-staging}"
TRAFFIC_PERCENT="${TRAFFIC_PERCENT:-10}"
DEPLOYMENT="${1:-dashboard}"

# Apply manifests for the desired environment
MANIFEST_DIR="k8s/canary"
if [[ "$TARGET_ENV" == "production" ]]; then
  MANIFEST_DIR="k8s/bluegreen"
fi

kubectl -n "$TARGET_ENV" apply -f "$MANIFEST_DIR" >/dev/null

# Annotate service to shape traffic for canary deployments
kubectl -n "$TARGET_ENV" annotate service "$DEPLOYMENT" \
  traffic.percent="$TRAFFIC_PERCENT" --overwrite >/dev/null

echo "Applied $MANIFEST_DIR with $TRAFFIC_PERCENT% traffic to $DEPLOYMENT in $TARGET_ENV"
