#!/usr/bin/env python3
"""Migrate PostgreSQL data from ``yosai_intel`` to ``yosai_timescale``.

The script copies tables using chunked inserts and validates each chunk via
row count and checksum comparison. Progress for the ``access_events`` table is
shown with ``tqdm``. A ``migration_checkpoint`` table stores the last processed
ID to allow resuming the migration.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import threading
import time
from typing import Any, Iterable, List, Mapping, Sequence, cast

import psycopg2
from psycopg2.extensions import connection, cursor
from psycopg2.extras import DictCursor, execute_batch
from tqdm import tqdm

CHUNK_SIZE = 10_000
CHECKPOINT_TABLE = "migration_checkpoint"


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
    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {CHECKPOINT_TABLE} (
            table_name TEXT PRIMARY KEY,
            last_id BIGINT
        )
        """
    )


def get_checkpoint(cur: cursor, table: str) -> int:
    cur.execute(
        f"SELECT last_id FROM {CHECKPOINT_TABLE} WHERE table_name = %s", (table,)
    )
    row = cur.fetchone()
    return row[0] if row else 0


def update_checkpoint(cur: cursor, table: str, last_id: int) -> None:
    cur.execute(
        f"""
        INSERT INTO {CHECKPOINT_TABLE} (table_name, last_id)
        VALUES (%s, %s)
        ON CONFLICT (table_name)
        DO UPDATE SET last_id = EXCLUDED.last_id
        """,
        (table, last_id),
    )


def rows_checksum(rows: Iterable[Mapping[str, Any] | Sequence[Any]]) -> str:
    m = hashlib.md5()
    for row in rows:
        m.update(str(tuple(row)).encode())
    return m.hexdigest()


# ---------------------------------------------------------------------------
# Migration helpers
# ---------------------------------------------------------------------------


def fetch_chunk(cur: cursor, table: str, start: int, size: int) -> List[dict[str, Any]]:
    cur.execute(
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
    target_cur.execute(
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
        if table == "access_events":
            src.execute(f"SELECT COUNT(*) FROM {table}")
            total = src.fetchone()[0]
            pbar = tqdm(total=total - last_id, desc=table)
        else:
            pbar = None
        while True:
            rows = fetch_chunk(src, table, last_id, CHUNK_SIZE)
            if not rows:
                break
            start_id = rows[0]["id"]
            last_id = rows[-1]["id"]
            checksum = rows_checksum(rows)
            if not test_mode:
                insert_rows(tgt, table, rows)
                validate_chunk(tgt, table, start_id - 1, last_id, checksum, len(rows))
                update_checkpoint(tgt, table, last_id)
                target_conn.commit()
            if pbar:
                pbar.update(len(rows))
            if test_mode:
                break
        if pbar:
            pbar.close()


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
        cur.execute("SELECT COUNT(*) FROM access_events")
        count = cur.fetchone()[0]
        print(f"access_events rows: {count}")
        cur.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema='public'"
        )
        tables = [r[0] for r in cur.fetchall()]
        print("Tables:", ", ".join(tables))
        cur.execute("SELECT * FROM timescaledb_information.compressed_hypertables")
        print("Compressed hypertables:")
        for row in cur.fetchall():
            print(row)


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
        migrate_table(src_conn, tgt_conn, "access_events", args.resume, args.test_mode)
        other_tables = ["users", "devices", "alerts"]
        migrate_other_tables(
            src_conn, tgt_conn, other_tables, args.resume, args.test_mode
        )
        if not args.test_mode:
            run_verification(tgt_conn)
    finally:
        src_conn.close()
        tgt_conn.close()


if __name__ == "__main__":
    main()
