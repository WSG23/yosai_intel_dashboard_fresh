from __future__ import annotations

"""Lightweight query optimization utilities."""

import logging
from typing import Any, Callable, List, Optional

from .base_model import BaseModel
from .query_optimizer import monitor_query_performance


class AdvancedQueryOptimizer(BaseModel):
    """Apply simple transformation rules to optimize queries."""

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Initialize optimizer with optional config, database and logger."""
        super().__init__(config, db, logger)
        self._rules: List[Callable[[str], str]] = []

    def register_rule(self, rule: Callable[[str], str]) -> None:
        """Register a query transformation rule."""
        self._rules.append(rule)

    @monitor_query_performance()
    def optimize(self, query: str) -> str:
        """Return the optimized query string."""
        optimized = query
        for rule in self._rules:
            try:
                optimized = rule(optimized)
            except Exception:  # pragma: no cover - best effort
                continue
        return optimized


__all__ = ["AdvancedQueryOptimizer"]
