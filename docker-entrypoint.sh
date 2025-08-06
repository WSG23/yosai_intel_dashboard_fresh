#!/usr/bin/env bash
set -e

CMD="$1"

# Default to start_api.py when no command or options provided
if [[ -z "$CMD" || "$CMD" == -* ]]; then
  exec python /app/start_api.py "$@"
fi

if [[ "$CMD" == "start_api.py" ]]; then
  shift
  exec python /app/start_api.py "$@"
fi

if [[ "$CMD" == "wsgi.py" ]]; then
  shift
  if python - <<'PY'
import importlib, sys
try:
    import wsgi  # noqa: F401
except Exception:
    sys.exit(1)
PY
  then
    exec python /app/wsgi.py "$@"
  else
    echo "wsgi import failed, falling back to start_api.py" >&2
    exec python /app/start_api.py "$@"
  fi
fi

# Fallback: execute whatever command was provided
exec "$CMD" "$@"
