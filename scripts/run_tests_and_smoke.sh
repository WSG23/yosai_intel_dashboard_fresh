#!/usr/bin/env bash
set -euo pipefail

echo "Running unit tests..."
if ! pytest --maxfail=1 --disable-warnings -q --cov=./ --cov-fail-under=80; then
    echo "❌ Unit tests failed"
    exit 1
fi

echo "✅ Unit tests passed"

exit 0
