#!/usr/bin/env python3
"""Migrate PostgreSQL data from ``yosai_intel`` to ``yosai_timescale``.

The script copies tables using chunked inserts and validates each chunk via
row count and checksum comparison. Progress for the ``access_events`` table is
shown with ``tqdm``. A ``migration_checkpoint`` table stores the last processed
ID to allow resuming the migration. Additional tables like ``people``, ``doors``
and ``facilities`` are included. Timestamp columns are converted to
``TIMESTAMPTZ`` and UUIDs are normalised. Metadata JSON is cleaned before
insertion. A ``--rollback`` option removes migrated data and checkpoints so the
migration can be restarted from scratch.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Iterable, List, Mapping, Sequence, cast

import psycopg2
from psycopg2.extensions import connection, cursor
from psycopg2.extras import DictCursor, execute_batch
from tqdm import tqdm

from database.secure_exec import execute_command, execute_query

CHUNK_SIZE = 10_000
CHECKPOINT_TABLE = "migration_checkpoint"

LOG = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------


def connect_with_retry(dsn: str, retries: int = 5, delay: float = 1.0) -> connection:
    """Return a new connection, retrying with exponential backoff."""
    attempt = 0
    while True:
        try:
            return psycopg2.connect(dsn)
        except psycopg2.OperationalError:
            attempt += 1
            if attempt > retries:
                raise
            time.sleep(delay * attempt)


def ensure_checkpoint_table(cur: cursor) -> None:
    execute_command(
        cur,
        f"""
        CREATE TABLE IF NOT EXISTS {CHECKPOINT_TABLE} (
            table_name TEXT PRIMARY KEY,
            last_id BIGINT
        )
        """,
    )


def get_checkpoint(cur: cursor, table: str) -> int:
    execute_query(
        cur,
        f"SELECT last_id FROM {CHECKPOINT_TABLE} WHERE table_name = %s",
        (table,),
    )
    row = cur.fetchone()
    return row[0] if row else 0


def update_checkpoint(cur: cursor, table: str, last_id: int) -> None:
    execute_command(
        cur,
        f"""
        INSERT INTO {CHECKPOINT_TABLE} (table_name, last_id)
        VALUES (%s, %s)
        ON CONFLICT (table_name)
        DO UPDATE SET last_id = EXCLUDED.last_id
        """,
        (table, last_id),
    )


def rollback_table(conn: connection, table: str) -> None:
    """Delete data and checkpoint for the given table."""
    with conn.cursor() as cur:
        ensure_checkpoint_table(cur)
        LOG.info("Rolling back table %s", table)
        execute_command(cur, f"DELETE FROM {table}")
        execute_command(
            cur,
            f"DELETE FROM {CHECKPOINT_TABLE} WHERE table_name = %s",
            (table,),
        )
    conn.commit()


def rows_checksum(rows: Iterable[Mapping[str, Any] | Sequence[Any]]) -> str:
    m = hashlib.md5()
    for row in rows:
        m.update(str(tuple(row)).encode())
    return m.hexdigest()


def normalize_row(row: dict[str, Any]) -> None:
    """Normalize timestamps, UUIDs and JSON metadata in-place."""
    for key, value in list(row.items()):
        if isinstance(value, datetime) and value.tzinfo is None:
            row[key] = value.replace(tzinfo=timezone.utc)
        elif isinstance(value, str):
            try:
                row[key] = str(uuid.UUID(value))
                continue
            except (ValueError, TypeError):
                pass
            try:
                obj = json.loads(value)
            except Exception:
                continue
            if isinstance(obj, dict):
                row[key] = {k: v for k, v in obj.items() if v is not None}
            else:
                row[key] = obj
        elif isinstance(value, dict):
            row[key] = {k: v for k, v in value.items() if v is not None}


def normalize_rows(rows: List[dict[str, Any]]) -> None:
    for row in rows:
        normalize_row(row)


def setup_timescale(conn: connection) -> None:
    """Ensure TimescaleDB extension and hypertable configuration."""
    with conn.cursor() as cur:
        # enable extension
        cur.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")

        # base table and hypertable
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS access_events (
                time TIMESTAMPTZ NOT NULL,
                event_id UUID PRIMARY KEY,
                person_id VARCHAR(50),
                door_id VARCHAR(50),
                facility_id VARCHAR(50),
                access_result VARCHAR(20),
                badge_status VARCHAR(20),
                response_time_ms INTEGER,
                metadata JSONB
            )
            """,
        )
        cur.execute(
            """
            SELECT create_hypertable(
                'access_events',
                'time',
                chunk_time_interval => INTERVAL '1 day',
                if_not_exists => TRUE
            )
            """
        )

        # indexes for common query patterns
        cur.execute(
            (
                "CREATE INDEX IF NOT EXISTS idx_access_events_person "
                "ON access_events(person_id)"
            )
        )
        cur.execute(
            (
                "CREATE INDEX IF NOT EXISTS idx_access_events_device "
                "ON access_events(door_id)"
            )
        )
        cur.execute(
            (
                "CREATE INDEX IF NOT EXISTS idx_access_events_location "
                "ON access_events(facility_id)"
            )
        )
        cur.execute(
            (
                "CREATE INDEX IF NOT EXISTS idx_access_events_decision "
                "ON access_events(access_result)"
            )
        )
        cur.execute(
            (
                "CREATE INDEX IF NOT EXISTS idx_access_events_metadata "
                "ON access_events USING GIN(metadata)"
            )
        )

        # continuous aggregate
        cur.execute("SELECT to_regclass('access_events_5min')")
        if cur.fetchone()[0] is None:
            cur.execute(
                """
                CREATE MATERIALIZED VIEW access_events_5min
                WITH (timescaledb.continuous) AS
                SELECT time_bucket('5 minutes', time) AS bucket,
                       COUNT(*) AS event_count
                FROM access_events
                GROUP BY bucket
                WITH NO DATA
                """
            )

        cur.execute(
            """
            SELECT add_continuous_aggregate_policy(
                'access_events_5min',
                schedule_interval => INTERVAL '5 minutes',
                start_offset => INTERVAL '90 days',
                end_offset => INTERVAL '1 hour',
                if_not_exists => TRUE
            )
            """
        )

        # compression and retention
        cur.execute(
            """
            ALTER TABLE access_events
                SET (
                    timescaledb.compress,
                    timescaledb.compress_orderby = 'time DESC',
                    timescaledb.compress_segmentby = 'facility_id'
                )
            """
        )
        cur.execute(
            """
            SELECT add_compression_policy(
                'access_events',
                INTERVAL '30 days',
                if_not_exists => TRUE
            )
            """
        )
        cur.execute(
            """
            SELECT add_retention_policy(
                'access_events',
                INTERVAL '365 days',
                if_not_exists => TRUE
            )
            """
        )
    conn.commit()


# ---------------------------------------------------------------------------
# Migration helpers
# ---------------------------------------------------------------------------


def fetch_chunk(cur: cursor, table: str, start: int, size: int) -> List[dict[str, Any]]:
    execute_query(
        cur,
        f"SELECT * FROM {table} WHERE id > %s ORDER BY id ASC LIMIT %s",
        (start, size),
    )
    return cast(List[dict[str, Any]], cur.fetchall())


def insert_rows(cur: cursor, table: str, rows: List[dict[str, Any]]) -> None:
    if not rows:
        return
    columns = rows[0].keys()
    values = [tuple(row[col] for col in columns) for row in rows]
    cols = ",".join(columns)
    placeholders = ",".join(["%s"] * len(columns))
    query = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
    execute_batch(cur, query, values)


def validate_chunk(
    target_cur: cursor,
    table: str,
    start_id: int,
    end_id: int,
    source_checksum: str,
    expected_count: int,
) -> None:
    execute_query(
        target_cur,
        f"SELECT * FROM {table} WHERE id > %s AND id <= %s ORDER BY id ASC",
        (start_id, end_id),
    )
    rows = target_cur.fetchall()
    if len(rows) != expected_count:
        raise ValueError(
            f"Row count mismatch for {table}: {len(rows)} != {expected_count}"
        )
    target_checksum = rows_checksum(rows)
    if target_checksum != source_checksum:
        raise ValueError("Checksum mismatch for {table}")


# ---------------------------------------------------------------------------
# Table migration
# ---------------------------------------------------------------------------


def migrate_table(
    source_conn: connection,
    target_conn: connection,
    table: str,
    resume: bool = False,
    test_mode: bool = False,
) -> None:
    with source_conn.cursor(cursor_factory=DictCursor) as src, target_conn.cursor(
        cursor_factory=DictCursor
    ) as tgt:
        ensure_checkpoint_table(tgt)
        last_id = get_checkpoint(tgt, table) if resume else 0
        LOG.info("Starting migration for %s at id %s", table, last_id)
        if table == "access_events":
            execute_query(src, f"SELECT COUNT(*) FROM {table}")
            total = src.fetchone()[0]
            pbar = tqdm(total=total - last_id, desc=table)
        else:
            pbar = None
        while True:
            rows = fetch_chunk(src, table, last_id, CHUNK_SIZE)
            if not rows:
                break
            normalize_rows(rows)
            start_id = rows[0]["id"]
            last_id = rows[-1]["id"]
            checksum = rows_checksum(rows)
            if not test_mode:
                insert_rows(tgt, table, rows)
                validate_chunk(tgt, table, start_id - 1, last_id, checksum, len(rows))
                update_checkpoint(tgt, table, last_id)
                target_conn.commit()
            LOG.info(
                "migrated %s rows for %s (id %s-%s)",
                len(rows),
                table,
                start_id,
                last_id,
            )
            if pbar:
                pbar.update(len(rows))
            if test_mode:
                break
        if pbar:
            pbar.close()
        LOG.info("Completed migration for %s", table)


def migrate_other_tables(
    source_conn: connection,
    target_conn: connection,
    tables: List[str],
    resume: bool,
    test_mode: bool,
) -> None:
    threads = []
    for table in tables:
        thread = threading.Thread(
            target=migrate_table,
            args=(source_conn, target_conn, table, resume, test_mode),
            name=f"migrate_{table}",
        )
        thread.start()
        threads.append(thread)
    for t in threads:
        t.join()


def run_verification(target_conn: connection) -> None:
    with target_conn.cursor() as cur:
        execute_query(cur, "SELECT COUNT(*) FROM access_events")
        count = cur.fetchone()[0]
        LOG.info("access_events rows: %s", count)
        execute_query(
            cur,
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public'",
        )
        tables = [r[0] for r in cur.fetchall()]
        LOG.info("Tables: %s", ", ".join(tables))
        execute_query(
            cur, "SELECT * FROM timescaledb_information.compressed_hypertables"
        )
        LOG.info("Compressed hypertables:")
        for row in cur.fetchall():
            LOG.info(str(row))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrate to TimescaleDB")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument(
        "--test-mode", action="store_true", help="Run a single chunk without writing"
    )
    parser.add_argument(
        "--rollback",
        action="store_true",
        help="Clear target tables and checkpoints before migrating",
    )
    parser.add_argument(
        "--source-dsn",
        default=os.getenv("SOURCE_DSN", "dbname=yosai_intel"),
        help="Connection string for source database",
    )
    parser.add_argument(
        "--target-dsn",
        default=os.getenv("TARGET_DSN", "dbname=yosai_timescale"),
        help="Connection string for target database",
    )
    args = parser.parse_args()

    src_conn = connect_with_retry(args.source_dsn)
    tgt_conn = connect_with_retry(args.target_dsn)

    try:
        setup_timescale(tgt_conn)
        all_tables = [
            "access_events",
            "users",
            "devices",
            "alerts",
            "people",
            "doors",
            "facilities",
            "anomaly_detections",
            "incident_tickets",
        ]
        if args.rollback:
            for table in all_tables:
                rollback_table(tgt_conn, table)
        migrate_table(src_conn, tgt_conn, "access_events", args.resume, args.test_mode)
        other_tables = [
            "users",
            "devices",
            "alerts",
            "people",
            "doors",
            "facilities",
            "anomaly_detections",
            "incident_tickets",
        ]
        migrate_other_tables(
            src_conn, tgt_conn, other_tables, args.resume, args.test_mode
        )
        if not args.test_mode:
            run_verification(tgt_conn)
    finally:
        src_conn.close()
        tgt_conn.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    main()
