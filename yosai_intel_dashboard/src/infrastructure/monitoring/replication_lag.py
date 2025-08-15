"""Prometheus metrics for logical replication lag."""

from prometheus_client import REGISTRY, Gauge
from prometheus_client.core import CollectorRegistry
import psycopg2

if "replication_lag_bytes" not in REGISTRY._names_to_collectors:
    replication_lag_bytes = Gauge(
        "replication_lag_bytes",
        "Bytes of WAL pending for a logical replication slot",
        ["slot"],
    )
else:  # pragma: no cover - defensive in tests
    replication_lag_bytes = Gauge(
        "replication_lag_bytes",
        "Bytes of WAL pending for a logical replication slot",
        ["slot"],
        registry=CollectorRegistry(),
    )

def record_replication_lag(dsn: str, slot_name: str) -> None:
    """Update the replication_lag_bytes gauge for *slot_name*.

    Parameters
    ----------
    dsn:
        Connection string for the source database.
    slot_name:
        Name of the logical replication slot to inspect.
    """
    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT pg_wal_lsn_diff(pg_current_wal_lsn(), confirmed_flush_lsn) "
            "FROM pg_replication_slots WHERE slot_name = %s",
            (slot_name,),
        )
        lag = cur.fetchone()
        if lag and lag[0] is not None:
            replication_lag_bytes.labels(slot=slot_name).set(float(lag[0]))
        else:
            replication_lag_bytes.labels(slot=slot_name).set(0)

__all__ = ["record_replication_lag", "replication_lag_bytes"]
