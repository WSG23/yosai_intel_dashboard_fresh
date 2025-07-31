from __future__ import annotations

"""Thin wrappers over shared analytics queries for the microservice."""

from typing import Any, Dict

import asyncpg

from yosai_intel_dashboard.src.services.analytics.common_queries import (
    fetch_access_patterns as _fetch_access_patterns,
)
from yosai_intel_dashboard.src.services.analytics.common_queries import (
    fetch_dashboard_summary as _fetch_dashboard_summary,
)


async def fetch_dashboard_summary(pool: asyncpg.Pool, days: int = 7) -> Dict[str, Any]:
    """Proxy to :func:`services.analytics.common_queries.fetch_dashboard_summary`."""
    return await _fetch_dashboard_summary(pool, days)


async def fetch_access_patterns(
    pool: asyncpg.Pool,
    days: int = 7,
    *,
    limit: int | None = None,
    offset: int | None = None,
) -> Dict[str, Any]:
    """Proxy to :func:`services.analytics.common_queries.fetch_access_patterns` with pagination."""
    return await _fetch_access_patterns(pool, days, limit=limit, offset=offset)


__all__ = ["fetch_dashboard_summary", "fetch_access_patterns"]
