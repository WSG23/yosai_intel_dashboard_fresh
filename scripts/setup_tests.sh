#!/usr/bin/env bash
set -euo pipefail
# Install Python dependencies required to run the test suite.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(realpath "$SCRIPT_DIR/..")"

if [ -d "$ROOT_DIR/packages" ]; then
  pip install --no-index --find-links "$ROOT_DIR/packages" -r "$ROOT_DIR/requirements-dev.txt"
else
  pip install -r "$ROOT_DIR/requirements-dev.txt"
fi
