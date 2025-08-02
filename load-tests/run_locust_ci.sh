#!/usr/bin/env bash
set -euo pipefail

DIR="$(dirname "$0")"
OUTPUT_DIR=${OUTPUT_DIR:-$DIR/results}
BASELINE=${BASELINE:-$DIR/baseline.json}

export OUTPUT_DIR
"$DIR/run_locust.sh"

python "$DIR/generate_report.py" "$OUTPUT_DIR/locust_stats.csv" "$BASELINE" "$OUTPUT_DIR"
python "$DIR/validate_thresholds.py" "$OUTPUT_DIR/locust_stats.csv" "$DIR/../config/performance_budgets.yml"
