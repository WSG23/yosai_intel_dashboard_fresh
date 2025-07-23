#!/usr/bin/env bash
set -euo pipefail

THRESHOLDS_FILE="$(dirname "$0")/thresholds.json"
FAILED_RATE=$(jq -r '.http_req_failed_rate' "$THRESHOLDS_FILE")
DURATION_P95=$(jq -r '.http_req_duration_p95' "$THRESHOLDS_FILE")

for f in "$@"; do
  rate=$(jq -r '.metrics.http_req_failed.rate' "$f")
  p95=$(jq -r '.metrics.http_req_duration["p(95)"]' "$f")

  if (( $(echo "$rate > $FAILED_RATE" | bc -l) )); then
    echo "Failure rate $rate exceeds threshold $FAILED_RATE for $f" >&2
    exit 1
  fi

  if (( $(echo "$p95 > $DURATION_P95" | bc -l) )); then
    echo "p95 duration $p95 exceeds threshold $DURATION_P95 for $f" >&2
    exit 1
  fi

done
