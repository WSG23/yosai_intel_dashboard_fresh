#!/usr/bin/env bash
set -e

echo "📊 Running load tests..."
python tests/performance/test_event_processing.py

exit 0
