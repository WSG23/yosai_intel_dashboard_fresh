#!/usr/bin/env bash
# Ensure no Kubernetes manifest uses :latest image tags.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

violations=$(grep -R --line-number ':latest' "$ROOT_DIR/k8s" || true)
if [[ -n "$violations" ]]; then
  echo "❌ Found :latest image tags in Kubernetes manifests:" >&2
  echo "$violations" >&2
  exit 1
fi

echo "✅ No :latest image tags found in Kubernetes manifests"
