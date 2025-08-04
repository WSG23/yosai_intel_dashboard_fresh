#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(dirname "$0")"
REPO_ROOT="$SCRIPT_DIR/.."
BUDGETS_FILE="$REPO_ROOT/config/performance_budgets.yml"
FAILED_RATE=$(python3 -c "import yaml,sys;print(yaml.safe_load(open('$BUDGETS_FILE'))['http_req_failed_rate'])")
DURATION_P95=$(python3 -c "import yaml,sys;print(yaml.safe_load(open('$BUDGETS_FILE'))['http_req_duration_p95'])")

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

python3 "$REPO_ROOT/tools/performance_report.py" "$@"
