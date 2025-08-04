#!/usr/bin/env bash
set -e

echo "📊 Running load tests..."
python3 tests/performance/test_event_processing.py

exit 0
