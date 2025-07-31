from __future__ import annotations

"""Tools for analysing database query performance.

The :class:`DatabasePerformanceAnalyzer` records timing information for
executed queries which can then be inspected for bottlenecks.
"""

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class DatabasePerformanceAnalyzer:
    """Collects performance metrics for executed database queries."""

    def __init__(self) -> None:
        self.query_metrics: List[Dict[str, Any]] = []

    def analyze_query_performance(self, query: str, execution_time: float) -> None:
        """Store execution time for a query."""
        logger.debug("Query executed in %.6f seconds: %s", execution_time, query)
        self.query_metrics.append({"query": query, "execution_time": execution_time})


__all__ = ["DatabasePerformanceAnalyzer"]
