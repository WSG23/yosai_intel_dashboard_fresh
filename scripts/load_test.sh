#!/usr/bin/env bash
set -euo pipefail

echo "📊 Running load tests..."
python3 tests/performance/test_event_processing.py

exit 0
