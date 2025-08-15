#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH=/app
if python -c "import uvicorn, itsdangerous, fastapi, dask.distributed, sqlalchemy" >/dev/null 2>&1; then
  python -m uvicorn --factory yosai_intel_dashboard.src.adapters.api.adapter:create_api_app --host 0.0.0.0 --port 8000 --reload
else
  if [ -f /app/wsgi.py ]; then python /app/wsgi.py; else exit 1; fi
fi
