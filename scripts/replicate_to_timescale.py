#!/usr/bin/env python3
"""Incrementally replicate new access events to TimescaleDB."""
from __future__ import annotations
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any

import psycopg2
from psycopg2.extras import DictCursor, execute_values
from prometheus_client import Gauge, start_http_server

LOG = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

SRC_DSN = os.getenv("SOURCE_DSN", "dbname=yosai_intel")
TGT_DSN = os.getenv("TARGET_DSN", "dbname=yosai_timescale")
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
    cur.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {CHECKPOINT_TABLE} (
            last_ts TIMESTAMPTZ PRIMARY KEY
        )
        """
    )
    cur.execute(
        f"INSERT INTO {CHECKPOINT_TABLE} (last_ts) VALUES ('1970-01-01') ON CONFLICT DO NOTHING"
    )


def get_last_timestamp(cur: DictCursor) -> str:
    cur.execute(f"SELECT last_ts FROM {CHECKPOINT_TABLE}")
    row = cur.fetchone()
    return row[0] if row else "1970-01-01"


def update_timestamp(cur: DictCursor, ts: str) -> None:
    cur.execute(f"UPDATE {CHECKPOINT_TABLE} SET last_ts = %s", (ts,))


def fetch_new_rows(cur: DictCursor, last_ts: str) -> list[dict[str, Any]]:
    cur.execute(
        "SELECT * FROM access_events WHERE time > %s ORDER BY time ASC LIMIT 1000",
        (last_ts,),
    )
    return cur.fetchall()


def insert_rows(cur: DictCursor, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    values = [tuple(row[f] for f in FIELDS) for row in rows]
    cols = ",".join(FIELDS)
    placeholders = ",".join(["%s"] * len(FIELDS))
    query = (
        f"INSERT INTO access_events ({cols}) VALUES ({placeholders})"
        " ON CONFLICT (event_id) DO NOTHING"
    )
    execute_values(cur, query, values)


def replicate_once(src, tgt) -> None:
    with tgt.cursor(cursor_factory=DictCursor) as tcur:
        ensure_checkpoint(tcur)
        last_ts = get_last_timestamp(tcur)
    with src.cursor(cursor_factory=DictCursor) as scur, tgt.cursor(cursor_factory=DictCursor) as tcur:
        rows = fetch_new_rows(scur, last_ts)
        if not rows:
            LOG.info("No new rows")
            return
        insert_rows(tcur, rows)
        new_ts = rows[-1]["time"]
        update_timestamp(tcur, new_ts)
        lag = (datetime.now(timezone.utc) - new_ts).total_seconds()
        replication_lag_seconds.set(lag)
        tgt.commit()
        LOG.info("Replicated %s rows (lag %.1fs)", len(rows), lag)


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
    main()
