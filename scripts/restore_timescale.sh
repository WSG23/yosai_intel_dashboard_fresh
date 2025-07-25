#!/usr/bin/env bash
set -euo pipefail

# Usage: TIMESCALE_DSN=<connection_string> ./scripts/restore_timescale.sh <backup_file>
# Restores a pg_dump archive created by backup_timescale.sh.

TGT_DSN="${TIMESCALE_DSN:-}"

if [[ $# -lt 1 ]]; then
  echo "Usage: TIMESCALE_DSN=<connection_string> $0 <backup_file>" >&2
  exit 1
fi

BACKUP_FILE="$1"

if [[ -z "$TGT_DSN" ]]; then
  echo "TIMESCALE_DSN environment variable not set" >&2
  exit 1
fi

if [[ ! -f "$BACKUP_FILE" ]]; then
  echo "Backup file $BACKUP_FILE not found" >&2
  exit 1
fi

echo "Restoring $BACKUP_FILE to $TGT_DSN"
pg_restore --clean --if-exists --no-owner --dbname "$TGT_DSN" "$BACKUP_FILE"

echo "Restore completed"

