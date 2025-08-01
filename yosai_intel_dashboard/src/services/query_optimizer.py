from __future__ import annotations

"""Analyze query plans and suggest potential indexes."""

import logging
import re
from typing import Any, Dict, Iterable, List, Sequence

from database.secure_exec import execute_query


logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Basic query plan analyzer that recommends indexes."""

    def __init__(self, connection: Any | None = None) -> None:
        if connection is None:
            from database.connection import create_database_connection

            connection = create_database_connection()
        self.connection = connection

    # ------------------------------------------------------------------
    def analyze_plan(self, query: str) -> List[str]:
        """Return the raw query plan for ``query``."""
        try:
            conn = self.connection
            name = conn.__class__.__name__
            if name == "SQLiteConnection":
                rows = execute_query(conn, f"EXPLAIN QUERY PLAN {query}")
                return [row.get("detail", "") for row in rows]
            if name == "PostgreSQLConnection":
                rows = execute_query(conn, f"EXPLAIN {query}")
                return [row.get("QUERY PLAN", "") for row in rows]
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("Failed to analyze plan: %s", exc)
        return []

    # ------------------------------------------------------------------
    def suggest_indexes(self, query: str) -> List[str]:
        """Return CREATE INDEX statements based on the query plan."""
        plan = self.analyze_plan(query)
        table, columns = self._extract_table_and_columns(query)
        statements: List[str] = []
        for col in columns:
            if self._needs_index(table, col, plan):
                statements.append(f"CREATE INDEX idx_{table}_{col} ON {table} ({col})")
        return statements

    # ------------------------------------------------------------------
    def generate_regression_report(self, query: str) -> Dict[str, Any]:
        """Return a regression report including index suggestions."""
        plan = self.analyze_plan(query)
        suggestions = self.suggest_indexes(query)
        return {"query": query, "plan": plan, "suggested_indexes": suggestions}

    # ------------------------------------------------------------------
    _TABLE_RE = re.compile(r"FROM\s+([\w\.]+)", re.IGNORECASE)
    _WHERE_RE = re.compile(r"WHERE\s+(.+)", re.IGNORECASE)
    _COND_RE = re.compile(r"\b(\w+)\s*=\s*[^\s]+", re.IGNORECASE)

    def _extract_table_and_columns(self, query: str) -> tuple[str, Sequence[str]]:
        table_match = self._TABLE_RE.search(query)
        table = table_match.group(1) if table_match else ""
        where_match = self._WHERE_RE.search(query)
        cols: List[str] = []
        if where_match:
            for cond in where_match.group(1).split("AND"):
                m = self._COND_RE.search(cond)
                if m:
                    cols.append(m.group(1))
        return table, cols

    # ------------------------------------------------------------------
    def _needs_index(self, table: str, column: str, plan: Iterable[str]) -> bool:
        for line in plan:
            if column in line and "INDEX" in line.upper():
                return False
        try:
            sql = (
                f"SELECT COUNT(DISTINCT {column}) AS distinct, COUNT(*) AS total "
                f"FROM {table}"
            )
            stats = execute_query(self.connection, sql)
            if not stats:
                return False
            row = stats[0]
            distinct = row.get("distinct") or row.get("DISTINCT") or 0
            total = row.get("total") or row.get("TOTAL") or 0
            if not total:
                return False
            return (distinct / total) > 0.1
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("Failed to fetch stats for %s.%s: %s", table, column, exc)
            return False


__all__ = ["QueryOptimizer"]

