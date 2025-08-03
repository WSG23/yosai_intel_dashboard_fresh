from __future__ import annotations

"""Database-specific query optimizer utilities."""

from functools import lru_cache
from typing import Callable


class DatabaseQueryOptimizer:
    """Inject simple optimizer hints for supported databases."""

    def __init__(self, db_type: str = "postgresql") -> None:
        self.db_type = db_type.lower()
        self._hint_func: Callable[[str], str]
        if self.db_type in {"postgresql", "postgres"}:
            self._hint_func = self._postgres_hint
        elif self.db_type == "sqlite":
            self._hint_func = self._sqlite_hint
        else:
            self._hint_func = lambda q: q

    # ------------------------------------------------------------------
    @lru_cache(maxsize=128)
    def optimize_query(self, query: str) -> str:
        """Return the optimized query with any hints applied.

        The query is first sanitized via :class:`UnicodeSQLProcessor` to
        ensure any surrogate or invalid Unicode data is handled safely
        before optimizer hints are injected.
        """

        from yosai_intel_dashboard.src.core.unicode import UnicodeSQLProcessor

        sanitized = UnicodeSQLProcessor.encode_query(query)
        return self._hint_func(sanitized)

    # ------------------------------------------------------------------
    def _postgres_hint(self, query: str) -> str:
        """Apply a basic PostgreSQL planner hint."""
        trimmed = query.lstrip()
        if trimmed.upper().startswith("SELECT") and "/*+" not in trimmed:
            return f"/*+ Parallel */ {query}"
        return query

    # ------------------------------------------------------------------
    def _sqlite_hint(self, query: str) -> str:
        """Apply a lightweight SQLite optimizer hint."""
        trimmed = query.lstrip()
        if trimmed.upper().startswith("SELECT") and "/*+" not in trimmed:
            return f"/*+ NO_INDEX */ {query}"
        return query


__all__ = ["DatabaseQueryOptimizer"]
