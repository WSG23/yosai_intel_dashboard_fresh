#!/usr/bin/env bash
set -euo pipefail

BASE_URL=${BASE_URL:-http://localhost:8000}
MODE=${MODE:-sustained}
RESULTS_DIR=${RESULTS_DIR:-load-tests/results}
METRICS_FILE=${METRICS_FILE:-$RESULTS_DIR/gatling_system_metrics.log}

BURST_USERS=${BURST_USERS:-100}
SUSTAINED_USERS=${SUSTAINED_USERS:-50}
BURST_DURATION=${BURST_DURATION:-30}
SUSTAINED_DURATION=${SUSTAINED_DURATION:-300}

mkdir -p "$RESULTS_DIR"

# Capture basic system metrics if vmstat is available
if command -v vmstat >/dev/null; then
  vmstat 1 > "$METRICS_FILE" &
  VMSTAT_PID=$!
else
  echo "vmstat not available; system metrics will not be captured" >&2
fi

export JAVA_OPTS="-DBASE_URL=$BASE_URL -DTEST_MODE=$MODE -DBURST_USERS=$BURST_USERS -DSUSTAINED_USERS=$SUSTAINED_USERS -DBURST_DURATION=$BURST_DURATION -DSUSTAINED_DURATION=$SUSTAINED_DURATION"

gatling -sf load-tests/gatling -s AnalyticsSimulation -rf "$RESULTS_DIR"

if [[ -n "${VMSTAT_PID:-}" ]]; then
  kill "$VMSTAT_PID" 2>/dev/null || true
fi
