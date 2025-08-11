#!/usr/bin/env bash
set -euo pipefail

: "${TIMEOUT:=30}"

require_env() {
  local var_name="$1"
  if [[ -z "${!var_name:-}" ]]; then
    echo "Environment variable ${var_name} is required" >&2
    exit 1
  fi
}

curl_with_timeout() {
  curl --fail --silent --show-error --max-time "${TIMEOUT}" "$@"
}
