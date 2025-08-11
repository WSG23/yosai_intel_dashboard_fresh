#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Wait for each URL passed as argument to return HTTP 200
for url in "$@"; do
  echo "Waiting for $url"
  for _ in {1..60}; do
    status=$(curl -s -o /dev/null -w "%{http_code}" "$url" || true)
    if [[ "$status" == "200" ]]; then
      echo "Service at $url is up"
      break
    fi
    sleep 2
  done
  if [[ "$status" != "200" ]]; then
    echo "Timed out waiting for $url"
    exit 1
  fi
done
