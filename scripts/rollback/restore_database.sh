#!/usr/bin/env bash
set -euo pipefail

BACKUP_FILE="${1:-}"
DB_DSN="${DB_DSN:-}"

if [[ -z "$BACKUP_FILE" || -z "$DB_DSN" ]]; then
  echo "Usage: DB_DSN=<connection_string> $0 <backup_file>" >&2
  exit 1
fi

echo "Restoring database from $BACKUP_FILE to $DB_DSN"
pg_restore --clean --if-exists --no-owner --dbname "$DB_DSN" "$BACKUP_FILE"
