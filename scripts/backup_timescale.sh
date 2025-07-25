#!/usr/bin/env bash
set -euo pipefail

# Usage: TIMESCALE_DSN=<connection_string> [OUTPUT_DIR=backups] [RETENTION_DAYS=7] ./scripts/backup_timescale.sh
# Creates a pg_dump archive and prunes old backups based on retention.

SRC_DSN="${TIMESCALE_DSN:-}"
OUTPUT_DIR="${OUTPUT_DIR:-backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

if [[ -z "$SRC_DSN" ]]; then
  echo "TIMESCALE_DSN environment variable not set" >&2
  exit 1
fi

if [[ $# -ge 1 ]]; then
  OUTPUT_DIR="$1"
fi

TIMESTAMP="$(date +"%Y%m%d_%H%M%S")"
mkdir -p "$OUTPUT_DIR"
BACKUP_FILE="$OUTPUT_DIR/timescale_${TIMESTAMP}.dump"

echo "Creating backup $BACKUP_FILE"
pg_dump --format=custom --file "$BACKUP_FILE" "$SRC_DSN"

echo "Verifying backup"
pg_restore --list "$BACKUP_FILE" >/dev/null

echo "Pruning backups older than $RETENTION_DAYS days"
find "$OUTPUT_DIR" -type f -name 'timescale_*.dump' -mtime "+$RETENTION_DAYS" -delete

echo "Backup complete: $BACKUP_FILE"

