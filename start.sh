#!/usr/bin/env bash
set -euo pipefail

if [ -f .env ]; then
  # shellcheck disable=SC1091
  source .env
fi

exec gunicorn -c gunicorn.conf.py wsgi:server
