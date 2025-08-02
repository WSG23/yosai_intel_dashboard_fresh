#!/usr/bin/env bash
set -euo pipefail

HOST=${HOST:-http://localhost:8000}
USERS=${USERS:-10}
SPAWN_RATE=${SPAWN_RATE:-2}
RUN_TIME=${RUN_TIME:-1m}
OUTPUT_DIR=${OUTPUT_DIR:-load-tests/results}

mkdir -p "$OUTPUT_DIR"

locust -f "$(dirname "$0")/locustfile.py" \
  --headless \
  --host "$HOST" \
  -u "$USERS" \
  -r "$SPAWN_RATE" \
  -t "$RUN_TIME" \
  --csv="$OUTPUT_DIR/locust" \
  --html="$OUTPUT_DIR/locust.html"
