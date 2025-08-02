"""Utilities to analyze database queries and recommend optimizations.

This module parses database logs looking for slow queries, retrieves
``EXPLAIN`` plans from the database and suggests potential indexes.  It also
tracks queries executed during a request to detect N+1 patterns.
"""

from __future__ import annotations

import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional

from yosai_intel_dashboard.src.database.connection import create_database_connection

logger = logging.getLogger(__name__)


@dataclass
class SlowQuery:
    """Representation of a slow query found in the logs."""

    query: str
    duration: float


class QueryOptimizer:
    """Analyze queries and provide optimization hints."""

    def __init__(self, connection: Optional[Any] = None) -> None:
        self.connection = connection or create_database_connection()
        # Track normalized queries to detect N+1 patterns
        self._query_counts: Dict[str, int] = defaultdict(int)

    # ------------------------------------------------------------------
    def parse_logs(self, log_path: str, threshold: float = 1.0) -> List[SlowQuery]:
        """Parse a database log file for slow queries.

        The function expects log lines containing ``duration: <ms>`` followed by
        ``statement: <SQL>`` similar to PostgreSQL logs.  Any query exceeding the
        ``threshold`` (in seconds) will be returned.
        """

        slow_queries: List[SlowQuery] = []
        line_re = re.compile(
            r"duration: (?P<ms>\d+\.?\d*) ms\s+statement: (?P<query>.*)",
            re.IGNORECASE,
        )
        try:
            with open(log_path, "r", encoding="utf8") as handle:
                for line in handle:
                    match = line_re.search(line)
                    if not match:
                        continue
                    duration_ms = float(match.group("ms"))
                    if duration_ms / 1000.0 >= threshold:
                        slow_queries.append(
                            SlowQuery(
                                query=match.group("query").strip(),
                                duration=duration_ms / 1000.0,
                            )
                        )
        except FileNotFoundError:
            logger.warning("Log file not found: %%s", log_path)
        return slow_queries

    # ------------------------------------------------------------------
    def get_explain_plan(self, query: str) -> List[Dict[str, Any]]:
        """Return the database EXPLAIN plan for ``query``."""
        try:
            df = self.connection.execute_query(f"EXPLAIN {query}")
            return df.to_dict("records")
        except Exception as exc:  # pragma: no cover - best effort
            logger.exception("Failed to get EXPLAIN plan: %%s", exc)
            return []

    # ------------------------------------------------------------------
    def recommend_indexes(self, plan: Iterable[Dict[str, Any]]) -> List[str]:
        """Generate simple index recommendations from an EXPLAIN plan."""
        recommendations: List[str] = []
        for row in plan:
            text = json.dumps(row)
            # Look for sequential scans which usually indicate missing indexes
            for table in re.findall(r"Seq Scan on (\w+)", text):
                recommendations.append(f"Consider adding an index on {table}")
        return recommendations

    # ------------------------------------------------------------------
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Return analysis details for a query including plan and suggestions."""
        plan = self.get_explain_plan(query)
        return {
            "plan": plan,
            "recommendations": self.recommend_indexes(plan),
        }

    # ------------------------------------------------------------------
    def track_query(self, query: str) -> bool:
        """Record query execution and detect N+1 patterns.

        Returns ``True`` if the query appears multiple times in the current
        scope which is a typical indicator of an N+1 problem.
        """

        normalized = self._normalize(query)
        self._query_counts[normalized] += 1
        return self._query_counts[normalized] > 1

    def reset_scope(self) -> None:
        """Reset tracking information for a new request scope."""
        self._query_counts.clear()

    # ------------------------------------------------------------------
    def _normalize(self, query: str) -> str:
        """Normalize a SQL query by stripping values for pattern matching."""
        normalized = re.sub(r"'[^']*'", "?", query)
        normalized = re.sub(r"\b\d+\b", "?", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized


__all__ = ["QueryOptimizer", "SlowQuery"]
