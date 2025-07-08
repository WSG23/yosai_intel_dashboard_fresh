#!/bin/bash
# Install only the Python dependencies required for running the tests.
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(realpath "$SCRIPT_DIR/..")"

pip install -r "$ROOT_DIR/requirements.txt" -r "$ROOT_DIR/requirements-test.txt"
