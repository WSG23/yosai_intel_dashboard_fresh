from __future__ import annotations

"""Lightweight query optimization utilities."""

from typing import Callable, List

from .query_optimizer import monitor_query_performance


class AdvancedQueryOptimizer:
    """Apply simple transformation rules to optimize queries."""

    def __init__(self) -> None:
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
