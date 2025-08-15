#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-}"
if [[ -z "$TARGET" ]]; then
  echo "Usage: $0 <migration-target>" >&2
  exit 1
fi

if ! command -v alembic >/dev/null 2>&1; then
  echo "alembic is required for database rollback" >&2
  exit 1
fi

# Use alembic to downgrade database to the specified migration
alembic downgrade "$TARGET"
