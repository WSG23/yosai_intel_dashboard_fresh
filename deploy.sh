#!/usr/bin/env bash
set -euo pipefail

if [[ "${1:-}" == "--dry-run" ]]; then
  echo "[DRY RUN] Would deploy image tag $(git rev-parse --short HEAD)"
  exit 0
fi

if [[ "${GENERATE_INDEX_MIGRATIONS:-}" == "1" ]]; then
  echo "Generating index migration script"
  python3 services/query_optimizer_cli.py migrate "SELECT 1" migrations/generated_indexes.sql || true
fi

echo "Deploying image tag $(git rev-parse --short HEAD)"
# Placeholder for real deployment commands

if [[ -n "${CDN_DISTRIBUTION_ID:-}" ]]; then
  echo "Invalidating CDN distribution $CDN_DISTRIBUTION_ID"
  aws cloudfront create-invalidation --distribution-id "$CDN_DISTRIBUTION_ID" --paths "/*"
fi

