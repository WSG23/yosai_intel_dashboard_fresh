#!/usr/bin/env bash
set -euo pipefail

METRIC_URL="${SLO_METRIC_URL:-http://prometheus/api/v1/query?query=error_rate}"
THRESHOLD="${SLO_ERROR_RATE_THRESHOLD:-0.05}"
NAMESPACE="${1:-staging}"
DEPLOYMENT="${2:-yosai-dashboard}"

error_rate=$(curl -sf "$METRIC_URL" || echo 0)

if python - <<PY 2>/dev/null; then
import sys
err=float(sys.argv[1]); thr=float(sys.argv[2])
print("breach" if err>thr else "ok")
PY
"$error_rate" "$THRESHOLD" | grep -q breach; then
  echo "SLO breach detected (error rate $error_rate > $THRESHOLD). Triggering rollback."
  "$(dirname "$0")/restore_images.sh" "$DEPLOYMENT" "$NAMESPACE"
else
  echo "SLO within limits (error rate $error_rate <= $THRESHOLD)."
fi
