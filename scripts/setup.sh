#!/bin/bash
# Install all Python dependencies required by the dashboard.
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(realpath "$SCRIPT_DIR/..")"
if [ -d "$ROOT_DIR/packages" ]; then
    # Install from local package directory when available
    pip install --no-index --find-links "$ROOT_DIR/packages" -r "$ROOT_DIR/requirements.txt"
    pip install --no-index --find-links "$ROOT_DIR/packages" -r "$ROOT_DIR/requirements-dev.txt"
else
    # Fallback to PyPI
    pip install -r "$ROOT_DIR/requirements.txt"
    pip install -r "$ROOT_DIR/requirements-dev.txt"
fi
