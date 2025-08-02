#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(dirname "$0")"
RESULTS_DIR="$SCRIPT_DIR/results"
mkdir -p "$RESULTS_DIR"

for scenario in "$SCRIPT_DIR"/k6/scenarios/*.js; do
  name=$(basename "$scenario" .js)
  k6 run --summary-export "$RESULTS_DIR/$name.json" "$scenario"
done

"$SCRIPT_DIR/check_thresholds.sh" "$RESULTS_DIR"/*.json
