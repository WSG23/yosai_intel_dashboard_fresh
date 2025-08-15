#!/usr/bin/env bash
set -euo pipefail

HOST=${HOST:-http://localhost:8000}
USERS=${USERS:-10}
SPAWN_RATE=${SPAWN_RATE:-2}
RUN_TIME=${RUN_TIME:-1m}
OUTPUT_DIR=${OUTPUT_DIR:-load-tests/results}

# Load pattern configuration
LOAD_TYPE=${LOAD_TYPE:-sustained}
BURST_USERS=${BURST_USERS:-100}
SUSTAINED_USERS=${SUSTAINED_USERS:-50}
BURST_DURATION=${BURST_DURATION:-30}
SUSTAINED_DURATION=${SUSTAINED_DURATION:-300}

# Metrics capture
METRICS_FILE=${METRICS_FILE:-$OUTPUT_DIR/system_metrics.csv}

export LOAD_TEST_TYPE="$LOAD_TYPE" BURST_USERS SUSTAINED_USERS BURST_DURATION SUSTAINED_DURATION METRICS_FILE

mkdir -p "$OUTPUT_DIR"

locust -f "$(dirname "$0")/locustfile.py" \
  --headless \
  --host "$HOST" \
  -u "$USERS" \
  -r "$SPAWN_RATE" \
  -t "$RUN_TIME" \
  --csv="$OUTPUT_DIR/locust" \
  --html="$OUTPUT_DIR/locust.html"
