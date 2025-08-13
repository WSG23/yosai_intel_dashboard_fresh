#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Load backup configuration
source "$SCRIPT_DIR/backup.conf"

# Ensure required variables are set
: "${TIMESCALE_DSN:?TIMESCALE_DSN is not set}"
OUTPUT_DIR="${OUTPUT_DIR:-backups}"
RETENTION_DAYS="${RETENTION_DAYS:-7}"

# Export for the backup script
export TIMESCALE_DSN OUTPUT_DIR RETENTION_DAYS
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Directory for Prometheus textfile exporter metrics
METRICS_DIR="${METRICS_DIR:-/var/lib/node_exporter/textfile_collector}"
METRICS_FILE="$METRICS_DIR/db_backup.prom"
mkdir -p "$METRICS_DIR"

if "$REPO_ROOT/scripts/backup_timescale.sh"; then
  {
    echo "backup_last_success_timestamp $(date +%s)"
    echo "backup_failures_total 0"
  } >"$METRICS_FILE"
else
  echo "backup_failures_total 1" >"$METRICS_FILE"
  exit 1
fi
