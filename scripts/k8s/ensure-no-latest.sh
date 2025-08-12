#!/usr/bin/env bash
set -euo pipefail

root="$(git rev-parse --show-toplevel)"

usage() {
  cat <<USAGE >&2
Usage: $(basename "$0") [DIRECTORY]

Ensures no ':latest' image tags are used in Kubernetes manifests under DIRECTORY.
DIRECTORY defaults to '${root}/deploy'.
USAGE
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" ]]; then
  usage
  exit 0
fi

dir="${1:-${root}/deploy}"

if [[ ! -d "$dir" ]]; then
  echo "Directory '$dir' does not exist." >&2
  exit 1
fi

if grep -R --include='*.yaml' --include='*.yml' -n ':latest' "$dir"; then
  echo "Error: ':latest' tag found in manifests under $dir" >&2
  exit 1
fi

exit 0
