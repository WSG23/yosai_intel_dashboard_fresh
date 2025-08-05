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

# Install Node dependencies for the CSS build step
if command -v npm >/dev/null 2>&1; then
    PUPPETEER_SKIP_DOWNLOAD=1 npm install
else
    echo "npm is not installed; skipping Node dependency installation" >&2
fi

# Apply database migrations
alembic -c "$ROOT_DIR/database/migrations/alembic.ini" upgrade head

# Optionally run a single replication cycle
if [ "$RUN_REPLICATION" = "1" ]; then
    python3 "$ROOT_DIR/scripts/replicate_to_timescale.py" &
fi
