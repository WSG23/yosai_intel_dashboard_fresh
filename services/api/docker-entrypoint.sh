#!/usr/bin/env bash
set -euo pipefail

log() {
  printf '[docker-entrypoint] %s\n' "$*"
}

start_fallback() {
  log "Starting fallback minimal app"
  python - <<'PY'
from http.server import BaseHTTPRequestHandler, HTTPServer

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Fallback app")

if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
PY
}

run_app() {
  local module="$1"
  log "Attempting to start ${module}"
  if out=$(python - <<PY 2>&1
import importlib
importlib.import_module("${module}")
PY
  ); then
    exec python -m "${module}"
  else
    log "$out"
    if echo "$out" | grep -qi "circular import"; then
      log "Circular import detected in ${module}. Retrying with cleared PYTHONPATH."
      if out=$(PYTHONPATH="" python - <<PY 2>&1
import importlib
importlib.import_module("${module}")
PY
      ); then
        exec PYTHONPATH="" python -m "${module}"
      else
        log "$out"
        return 1
      fi
    else
      return 1
    fi
  fi
}

run_app services.api.wsgi || run_app services.api.start_api || start_fallback
