#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<USAGE
Usage: $0 [--postgres DSN] [--timescale DSN] [--tables tbl1,tbl2] [--hash]

Compare row counts or hashes for tables in PostgreSQL and TimescaleDB.
Connection strings may also be provided via POSTGRES_DSN and TIMESCALE_DSN.
USAGE
}

PG_DSN="${POSTGRES_DSN:-}"
TS_DSN="${TIMESCALE_DSN:-}"
TABLES=(events metrics)
USE_HASH=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --postgres|-p)
      PG_DSN="$2"
      shift 2
      ;;
    --timescale|-t)
      TS_DSN="$2"
      shift 2
      ;;
    --tables|-T)
      IFS=',' read -r -a TABLES <<< "$2"
      shift 2
      ;;
    --hash|-H)
      USE_HASH=true
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac

done

if [[ -z "$PG_DSN" || -z "$TS_DSN" ]]; then
  echo "POSTGRES_DSN and TIMESCALE_DSN must be set via flags or environment variables" >&2
  usage >&2
  exit 1
fi

mismatch=false

for tbl in "${TABLES[@]}"; do
  if $USE_HASH; then
    query="SELECT md5(COALESCE(string_agg(md5(t::text), ''), '')) FROM \"$tbl\" t"
  else
    query="SELECT COUNT(*) FROM \"$tbl\""
  fi

  pg_val=$(psql "$PG_DSN" -Atc "$query" 2>/dev/null) || {
    echo "Failed to query $tbl in PostgreSQL" >&2
    mismatch=true
    continue
  }
  ts_val=$(psql "$TS_DSN" -Atc "$query" 2>/dev/null) || {
    echo "Failed to query $tbl in TimescaleDB" >&2
    mismatch=true
    continue
  }

  if [[ "$pg_val" != "$ts_val" ]]; then
    echo "Mismatch for table '$tbl': postgres=$pg_val timescale=$ts_val"
    mismatch=true
  fi
done

if $mismatch; then
  exit 1
else
  echo "All tables consistent: ${TABLES[*]}"
fi
