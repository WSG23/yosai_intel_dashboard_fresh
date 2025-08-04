#!/usr/bin/env python3
"""Incrementally replicate new access events to TimescaleDB."""
from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

import psycopg2
from prometheus_client import Gauge, start_http_server
from psycopg2.extras import DictCursor, execute_values

from database.secure_exec import execute_command, execute_query
from infrastructure.security.query_builder import SecureQueryBuilder
from yosai_intel_dashboard.src.services.common.secrets import get_secret

LOG = logging.getLogger(__name__)


def _resolve_dsn(value: str | None, field: str) -> str:
    if value:
        if value.startswith("vault:"):
            return get_secret(value[len("vault:") :])
        return value
    return get_secret(f"secret/data/timescale#{field}")


SRC_DSN = _resolve_dsn(os.getenv("SOURCE_DSN"), "source")
TGT_DSN = _resolve_dsn(os.getenv("TARGET_DSN"), "target")
POLL_INTERVAL = int(os.getenv("REPLICATION_INTERVAL", "60"))
METRICS_PORT = int(os.getenv("REPLICATION_METRICS_PORT", "8004"))

replication_lag_seconds = Gauge(
    "replication_lag_seconds",
    "Seconds between NOW() and the newest replicated event timestamp",
)

CHECKPOINT_TABLE = "replication_state"

FIELDS = [
    "time",
    "event_id",
    "person_id",
    "door_id",
    "facility_id",
    "access_result",
    "badge_status",
    "response_time_ms",
    "metadata",
]


def ensure_checkpoint(cur: DictCursor) -> None:
    builder = SecureQueryBuilder(allowed_tables={CHECKPOINT_TABLE})
    table = builder.table(CHECKPOINT_TABLE)
    sql, _ = builder.build(
        f"""
        CREATE TABLE IF NOT EXISTS {table} (
            last_ts TIMESTAMPTZ PRIMARY KEY
        )
        """,
        logger=LOG,
    )
    execute_command(cur, sql)
    sql2, params2 = builder.build(
        f"INSERT INTO {table} (last_ts) VALUES (%s) ON CONFLICT DO NOTHING",
        ("1970-01-01",),
        logger=LOG,
    )
    execute_command(cur, sql2, params2)


def get_last_timestamp(cur: DictCursor) -> datetime:
    builder = SecureQueryBuilder(allowed_tables={CHECKPOINT_TABLE})
    table = builder.table(CHECKPOINT_TABLE)
    sql, _ = builder.build(f"SELECT last_ts FROM {table}", logger=LOG)
    execute_query(cur, sql)
    row = cur.fetchone()
    if row:
        return row[0]
    return datetime.fromtimestamp(0, timezone.utc)


def update_timestamp(cur: DictCursor, ts: datetime) -> None:
    builder = SecureQueryBuilder(allowed_tables={CHECKPOINT_TABLE})
    table = builder.table(CHECKPOINT_TABLE)
    sql, params = builder.build(f"UPDATE {table} SET last_ts = %s", (ts,), logger=LOG)
    execute_command(cur, sql, params)


def fetch_new_rows(cur: DictCursor, last_ts: datetime) -> list[dict[str, Any]]:
    builder = SecureQueryBuilder(
        allowed_tables={"access_events"}, allowed_columns={"time"}
    )
    table = builder.table("access_events")
    time_col = builder.column("time")
    sql, params = builder.build(
        f"SELECT * FROM {table} WHERE {time_col} > %s ORDER BY {time_col} ASC LIMIT 1000",
        (last_ts,),
        logger=LOG,
    )
    execute_query(cur, sql, params)
    return cur.fetchall()


def insert_rows(cur: DictCursor, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    values = (tuple(row[f] for f in FIELDS) for row in rows)
    builder = SecureQueryBuilder(
        allowed_tables={"access_events"}, allowed_columns=set(FIELDS)
    )
    table = builder.table("access_events")
    cols = ",".join(builder.column(f) for f in FIELDS)
    placeholders = ",".join("%s" for _ in FIELDS)
    query = (
        f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
        " ON CONFLICT (event_id) DO NOTHING"
    )
    sql, _ = builder.build(query, logger=LOG)
    execute_values(cur, sql, values)


def replicate_once(src, tgt) -> None:
    with tgt.cursor(cursor_factory=DictCursor) as tcur:
        ensure_checkpoint(tcur)
        last_ts = get_last_timestamp(tcur)

    with src.cursor(cursor_factory=DictCursor) as scur, tgt.cursor(
        cursor_factory=DictCursor
    ) as tcur:
        rows = fetch_new_rows(scur, last_ts)
        if rows:
            insert_rows(tcur, rows)
            last_ts = rows[-1]["time"]
            update_timestamp(tcur, last_ts)
            LOG.info("Replicated %s rows", len(rows))
        else:
            LOG.info("No new rows")

        lag = (datetime.now(timezone.utc) - last_ts).total_seconds()
        replication_lag_seconds.set(lag)
        tgt.commit()
        LOG.info("Replication lag %.1fs", lag)


def main() -> None:
    src_conn = psycopg2.connect(SRC_DSN)
    tgt_conn = psycopg2.connect(TGT_DSN)
    start_http_server(METRICS_PORT)
    try:
        while True:
            replicate_once(src_conn, tgt_conn)
            time.sleep(POLL_INTERVAL)
    finally:
        src_conn.close()
        tgt_conn.close()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    main()
