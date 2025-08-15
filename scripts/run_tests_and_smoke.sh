#!/usr/bin/env bash
set -euo pipefail

echo "Running critical path tests..."
pytest tests/services/test_token_endpoint.py tests/test_feature_pipeline.py -q

echo "Running unit tests with coverage..."
if ! pytest --maxfail=1 --disable-warnings -q --cov=./ --cov-report=term-missing --cov-report=xml --cov-fail-under=80; then
    echo "❌ Unit tests failed"
    exit 1
fi

echo "✅ Unit tests passed"

exit 0
