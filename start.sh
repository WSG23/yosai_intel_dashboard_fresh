#!/usr/bin/env bash
set -euo pipefail

if [ -f .env ]; then
  # export variables from the file so subprocesses see them
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi
gunicorn -c gunicorn.conf.py wsgi:server
