"""Storage utilities for environmental context information.

The Yōsai Intel Dashboard can persist context data (weather, events,
social signals) for later analysis.  A small TimescaleDB helper is
provided.  The implementation is deliberately lightweight and falls back
to an in-memory store if the optional :mod:`psycopg2` dependency is not
available.  This keeps unit tests isolated from external services while
allowing real deployments to use a proper time-series database.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

try:  # pragma: no cover - optional dependency
    import psycopg2
    from psycopg2.extras import Json
except Exception:  # pragma: no cover - if psycopg2 missing
    psycopg2 = None  # type: ignore
    Json = None  # type: ignore


@dataclass
class StoredContext:
    """Representation of a stored context row."""

    timestamp: datetime
    data: Dict[str, Any]


class InMemoryContextStore:
    """Fallback store used when no database is configured."""

    def __init__(self) -> None:
        self._rows: List[StoredContext] = []

    def save(self, data: Dict[str, Any]) -> None:
        self._rows.append(StoredContext(datetime.utcnow(), data))

    def all(self) -> List[StoredContext]:
        return list(self._rows)


class TimescaleContextStore:
    """Persist context records into a TimescaleDB instance.

    The connection string should be provided via the ``CONTEXT_DB_DSN``
    environment variable (e.g. ``postgresql://user:pass@host/db``).  The
    target table must have the schema::

        CREATE TABLE IF NOT EXISTS environmental_context (
            ts TIMESTAMPTZ NOT NULL,
            payload JSONB NOT NULL
        );

    In production deployments this table can be converted into a
    hypertable using TimescaleDB's ``create_hypertable`` function.
    """

    def __init__(self, dsn: str | None = None) -> None:
        self.dsn = dsn or os.environ.get("CONTEXT_DB_DSN", "")
        self._conn = None

    def _connection(self):  # pragma: no cover - trivial wrapper
        if self._conn is None:
            if not psycopg2:
                raise RuntimeError("psycopg2 is required for TimescaleContextStore")
            self._conn = psycopg2.connect(self.dsn)
        return self._conn

    def save(self, data: Dict[str, Any]) -> None:
        conn = self._connection()
        with conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO environmental_context (ts, payload) VALUES (NOW(), %s)",
                [Json(data)],
            )

    def close(self) -> None:
        """Close the underlying database connection if it exists."""

        if self._conn is not None:
            try:
                self._conn.close()  # type: ignore[call-arg]
            finally:
                self._conn = None

    # Support usage as a context manager to guarantee cleanup
    def __enter__(self) -> "TimescaleContextStore":  # pragma: no cover - simple
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:  # pragma: no cover - simple
        self.close()
        return False
