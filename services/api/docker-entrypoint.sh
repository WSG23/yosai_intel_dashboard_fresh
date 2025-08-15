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
  local script="$1"
  local module="${script%.py}"
  log "Attempting to start ${script}"
  if out=$(python - <<PY 2>&1
import importlib
importlib.import_module("${module}")
PY
  ); then
    exec python "${script}"
  else
    log "$out"
    if echo "$out" | grep -qi "circular import"; then
      log "Circular import detected in ${script}. Retrying with cleared PYTHONPATH."
      if out=$(PYTHONPATH="" python - <<PY 2>&1
import importlib
importlib.import_module("${module}")
PY
      ); then
        exec PYTHONPATH="" python "${script}"
      else
        log "$out"
        return 1
      fi
    else
      return 1
    fi
  fi
}

run_app wsgi.py || run_app start_api.py || start_fallback
