from __future__ import annotations

"""Helpers for analyzing and creating database indexes."""

import logging
from typing import Any, List, Sequence

from database.types import DBRows

# Importing create_database_connection at module level pulls in heavy
# configuration dependencies which complicates testing.  To keep the module
# lightweight we defer that import until runtime when needed.
from .secure_exec import execute_command, execute_query

logger = logging.getLogger(__name__)


class IndexOptimizer:
    """Simple database index optimizer."""

    def __init__(self, connection: Any | None = None) -> None:
        if connection is None:
            from .connection import create_database_connection

            self.connection = create_database_connection()
        else:
            self.connection = connection

    # ------------------------------------------------------------------
    def analyze_index_usage(self) -> DBRows:
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
    def apply_recommendations(self, table: str, columns: Sequence[str]) -> None:
        """Execute any missing index recommendations for ``table``."""
        try:
            conn = self.connection
            for stmt in self.recommend_new_indexes(table, columns):
                execute_command(conn, stmt)
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("Failed to apply index recommendations: %s", exc)

    # ------------------------------------------------------------------
    def recommend_new_indexes(self, table: str, columns: Sequence[str]) -> List[str]:
        """Return CREATE INDEX statements for missing indexes."""
        try:
            conn = self.connection
            conn_name = conn.__class__.__name__
            index_name = f"idx_{table}_{'_'.join(columns)}"
            existing: List[str] = []
            if conn_name == "SQLiteConnection":
                rows: DBRows = execute_query(conn, "PRAGMA index_list(?)", (table,))
                existing = [row.get("name") for row in rows]
            elif conn_name == "PostgreSQLConnection":
                rows: DBRows = execute_query(
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
