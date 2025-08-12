#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

require() {
  for cmd in "$@"; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
      echo "Command '$cmd' is required but not installed" >&2
      exit 1
    fi
  done
}
