from __future__ import annotations

"""Helpers for analyzing and creating database indexes."""

import logging
from typing import Any, Dict, List, Sequence

from .connection import create_database_connection
from .secure_exec import execute_query

logger = logging.getLogger(__name__)


class IndexOptimizer:
    """Simple database index optimizer."""

    def __init__(self, connection: Any | None = None) -> None:
        self.connection = connection or create_database_connection()

    # ------------------------------------------------------------------
    def analyze_index_usage(self) -> List[Dict[str, Any]]:
        """Return index usage statistics for supported databases."""
        try:
            conn = self.connection
            conn_name = conn.__class__.__name__
            if conn_name == "SQLiteConnection":
                return execute_query(
                    conn, "SELECT name AS index_name, stat FROM sqlite_stat1"
                )
            if conn_name == "PostgreSQLConnection":
                return execute_query(
                    conn,
                    """SELECT pg_class.relname AS index_name, idx_scan, idx_tup_read, idx_tup_fetch\n                       FROM pg_stat_user_indexes\n                       JOIN pg_class ON pg_stat_user_indexes.indexrelid = pg_class.oid""",
                )
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("Failed to analyze index usage: %s", exc)
        return []

    # ------------------------------------------------------------------
    def recommend_new_indexes(self, table: str, columns: Sequence[str]) -> List[str]:
        """Return CREATE INDEX statements for missing indexes."""
        try:
            conn = self.connection
            conn_name = conn.__class__.__name__
            index_name = f"idx_{table}_{'_'.join(columns)}"
            existing: List[str] = []
            if conn_name == "SQLiteConnection":
                rows = execute_query(conn, "PRAGMA index_list(?)", (table,))
                existing = [row.get("name") for row in rows]
            elif conn_name == "PostgreSQLConnection":
                rows = execute_query(
                    conn,
                    "SELECT indexname FROM pg_indexes WHERE tablename=%s",
                    (table,),
                )
                existing = [row.get("indexname") for row in rows]
            else:
                return []
            if index_name not in existing:
                cols = ", ".join(columns)
                return [f"CREATE INDEX {index_name} ON {table} ({cols})"]
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("Failed to recommend indexes: %s", exc)
        return []


__all__ = ["IndexOptimizer"]
