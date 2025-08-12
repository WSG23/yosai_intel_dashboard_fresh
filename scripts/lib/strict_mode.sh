# shellcheck shell=bash
# Provides common strict-mode settings and a `require` helper.
set -euo pipefail
IFS=$'\n\t'

require() {
  local cmd
  for cmd in "$@"; do
    if ! command -v "$cmd" >/dev/null 2>&1; then
      printf "Command '%s' is required but not installed\n" "$cmd" >&2
      return 1
    fi
  done
}

