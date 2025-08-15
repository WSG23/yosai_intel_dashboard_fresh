"""Factory helpers for the dashboard."""

from __future__ import annotations

import asyncio

from .db_health import DBHealthStatus


def health_check() -> DBHealthStatus:
    """Return database health status synchronously.

    Wraps the asynchronous ``services.common.async_db.health_check``
    so that call sites (like Flask endpoints) can retrieve the
    status without needing an event loop.
    """

    from yosai_intel_dashboard.src.services.common import async_db as _async_db

    return asyncio.run(_async_db.health_check())


__all__ = ["DBHealthStatus", "health_check"]
