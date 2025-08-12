#!/usr/bin/env bash
set -euo pipefail

SCRIPTDIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"

COMMON_SH="$SCRIPTDIR/../common.sh"
if [[ -f "$COMMON_SH" ]]; then
  # shellcheck disable=SC1090
  source "$COMMON_SH"
else
  echo "Warning: common.sh not found at $COMMON_SH" >&2
fi

TARGET_DIR="${1:-$SCRIPTDIR/../../k8s}"
if grep -R --line-number --exclude-dir='.git' -e ':latest' "$TARGET_DIR"; then
  echo "Error: 'latest' tag found in Kubernetes manifests" >&2
  exit 1
fi
