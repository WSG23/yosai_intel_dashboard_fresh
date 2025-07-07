#!/usr/bin/env bash
set -euo pipefail

echo "Running unit tests..."
if ! pytest --maxfail=1 --disable-warnings -q --cov=./; then
    echo "❌ Unit tests failed"
    exit 1
fi

echo "✅ Unit tests passed"

echo "Running smoke test..."
python -m file_processing.orchestrator \
  --file_path examples/sample_access_events.csv \
  --output_base tests/output/smoke_test \
  --hint '{}' \
  --config config/config.yaml \
  --device_registry config/device_registry.json \
  --callback_controller settings/callback_config.yaml

if [ ! -s tests/output/smoke_test.csv ] || [ ! -s tests/output/smoke_test.json ]; then
    echo "❌ Smoke test failed: missing or empty outputs"
    exit 1
fi

echo "✅ Smoke test passed"
exit 0
