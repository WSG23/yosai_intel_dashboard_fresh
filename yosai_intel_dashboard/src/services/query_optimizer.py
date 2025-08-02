"""N+1 query detection utilities."""

from __future__ import annotations

import logging
import traceback
from collections import defaultdict
from contextvars import ContextVar
from typing import Dict, List

from yosai_intel_dashboard.src.core.performance import profiler


logger = logging.getLogger(__name__)


# Context variable to store queries executed during a request
_request_queries: ContextVar[Dict[str, List[str]]] = ContextVar(
    "n_plus_one_queries", default=None
)


def _normalize_query(query: str) -> str:
    """Normalize query string to compare structural similarity."""
    import re

    normalized = re.sub(r"'[^']*'", "'?'", query)
    normalized = re.sub(r"\b\d+\b", "?", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def start_request_tracking() -> None:
    """Begin tracking queries for the current request."""
    _request_queries.set(defaultdict(list))


def track_query(query: str) -> None:
    """Record a query execution for N+1 detection."""
    queries = _request_queries.get()
    if queries is None:
        return

    pattern = _normalize_query(query)
    stack = "".join(traceback.format_stack(limit=5))
    queries[pattern].append(stack)


def end_request_tracking(endpoint: str) -> Dict[str, List[str]]:
    """Stop tracking and report any N+1 query patterns.

    Returns mapping of offending query pattern to stack traces.
    """

    queries = _request_queries.get()
    if not queries:
        return {}

    n_plus_one = {q: stacks for q, stacks in queries.items() if len(stacks) > 1}
    if n_plus_one:
        for query, stacks in n_plus_one.items():
            profiler.record_n_plus_one(endpoint, query, stacks)
            logger.warning("N+1 query detected on %s: %s", endpoint, query)
            for stack in stacks:
                logger.debug("Stack trace:\n%s", stack)

    _request_queries.set(None)
    return n_plus_one


__all__ = [
    "start_request_tracking",
    "track_query",
    "end_request_tracking",
]
