from __future__ import annotations

"""Helpers for Redis clients used on hot-path data."""

import os
from typing import Optional

import redis

_session_client: Optional[redis.Redis] = None
_metrics_client: Optional[redis.Redis] = None


def _create_client(url: str) -> redis.Redis:
    """Create a Redis client from a URL."""
    return redis.Redis.from_url(url)


def get_session_client() -> redis.Redis:
    """Return Redis client for session token storage.

    The URL is read from ``SESSION_REDIS_URL`` with a fallback to ``REDIS_URL``
    and finally ``redis://localhost:6379/0``.
    """

    global _session_client
    if _session_client is None:
        url = os.getenv("SESSION_REDIS_URL") or os.getenv(
            "REDIS_URL", "redis://localhost:6379/0"
        )
        _session_client = _create_client(url)
    return _session_client


def get_metrics_client() -> redis.Redis:
    """Return Redis client for recent metrics caching.

    The URL is read from ``METRICS_REDIS_URL`` with a fallback to ``REDIS_URL``
    and finally ``redis://localhost:6379/1`` (separate DB from session data).
    """

    global _metrics_client
    if _metrics_client is None:
        url = os.getenv("METRICS_REDIS_URL") or os.getenv(
            "REDIS_URL", "redis://localhost:6379/1"
        )
        _metrics_client = _create_client(url)
    return _metrics_client


# Backwards compatibility for modules expecting ``redis_client``.
# This points to the session client since it's the primary hot path.
redis_client = get_session_client()

__all__ = [
    "get_session_client",
    "get_metrics_client",
    "redis_client",
]
