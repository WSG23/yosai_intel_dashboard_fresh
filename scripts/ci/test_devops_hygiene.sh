#!/usr/bin/env bash
# Run DevOps hygiene checks: shellcheck, hadolint, Kubernetes manifest validation.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT_DIR"

# Shellcheck
mapfile -t sh_files < <(git ls-files '*.sh')
if (( ${#sh_files[@]} > 0 )); then
  shellcheck "${sh_files[@]}"
else
  echo "No shell scripts to lint"
fi

# Hadolint
mapfile -t dockerfiles < <(git ls-files '*Dockerfile*' Dockerfile)
if (( ${#dockerfiles[@]} > 0 )); then
  for df in "${dockerfiles[@]}"; do
    echo "Linting $df with hadolint"
    hadolint --config infra/.hadolint.yaml "$df"
  done
else
  echo "No Dockerfiles to lint"
fi

# Kubernetes manifest checks
./scripts/k8s/ensure-no-latest.sh
