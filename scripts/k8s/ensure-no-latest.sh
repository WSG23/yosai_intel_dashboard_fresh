#!/usr/bin/env bash
set -euo pipefail
IFS=$'\n\t'

# Ensure yq is available. Attempt installation if missing.
if ! command -v yq >/dev/null 2>&1; then
  if command -v apt-get >/dev/null 2>&1; then
    apt-get update >/dev/null
    apt-get install -y yq >/dev/null
  else
    pip install --user yq >/dev/null
    export PATH="$HOME/.local/bin:$PATH"
  fi
fi

ROOT_DIR="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
if [[ $# -gt 0 ]]; then
  TARGET_DIRS=("$@")
else
  TARGET_DIRS=("$ROOT_DIR/k8s")
fi

error=0
while IFS= read -r -d '' file; do
  if ! images=$(yq -r '..|.image? // empty' "$file" 2>/dev/null); then
    echo "Skipping non-YAML or templated file: $file" >&2
    continue
  fi
  while IFS= read -r image; do
    if [[ "$image" == *":latest"* ]]; then
      echo "${file}: contains disallowed :latest tag -> ${image}" >&2
      error=1
    fi
  done <<< "$images"
done < <(find "${TARGET_DIRS[@]}" -type f \( -name '*.yml' -o -name '*.yaml' \) -print0)

if [[ "$error" -eq 1 ]]; then
  echo "ERROR: Found image references with :latest tag" >&2
  exit 1
fi

echo "No :latest tags found in image fields."
