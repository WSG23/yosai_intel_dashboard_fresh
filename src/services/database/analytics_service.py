"""Asynchronous analytics helpers using a shared connection pool.

The previous implementation issued raw SQL strings directly against
database connections which made it easy to accidentally introduce SQL
injection vulnerabilities.  This module now relies on SQLAlchemy's
``text`` construct and parameter binding which ensures that any dynamic
values are safely escaped.  Connection pooling is centralised via the
``build_async_engine`` factory so all services share the same
``AsyncEngine`` instance.
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from yosai_intel_dashboard.src.database.async_engine_factory import build_async_engine

try:  # optional import to keep tests lightweight
    from yosai_intel_dashboard.src.infrastructure.config import get_database_config
except Exception:  # pragma: no cover - minimal stub for tests
    def get_database_config():  # type: ignore
        class _Cfg:
            type = "sqlite"
            async_pool_min_size = 1
            async_pool_max_size = 1
            async_connection_timeout = 30

            def get_connection_string(self) -> str:
                return "sqlite+aiosqlite:///:memory:"

        return _Cfg()


class AnalyticsService:
    """Retrieve analytics information using parameterised queries."""

    def __init__(
        self, session_factory: async_sessionmaker[AsyncSession] | None = None
    ) -> None:
        if session_factory is None:
            engine: AsyncEngine = build_async_engine(get_database_config())
            session_factory = async_sessionmaker(engine, expire_on_commit=False)
        self._session_factory = session_factory

    async def _fetch_user_count(self, session: AsyncSession) -> int:
        result = await session.execute(text("SELECT COUNT(*) AS count FROM users"))
        row = result.mappings().first()
        return int(row["count"]) if row else 0

    async def _fetch_recent_events(
        self, session: AsyncSession, *, limit: int = 10
    ) -> List[Dict[str, Any]]:
        stmt = text(
            "SELECT event_type, status, timestamp "
            "FROM access_events ORDER BY timestamp DESC LIMIT :limit"
        )
        result = await session.execute(stmt, {"limit": limit})
        return [dict(r) for r in result.mappings()]

    async def get_analytics(self, *, limit: int = 10) -> Dict[str, Any]:
        """Return basic analytics information.

        Parameters
        ----------
        limit:
            Maximum number of recent events to return.  Provided values are
            bound as parameters preventing SQL injection.
        """

        async with self._session_factory() as session:
            user_count, recent_events = await asyncio.gather(
                self._fetch_user_count(session),
                self._fetch_recent_events(session, limit=limit),
            )

        return {
            "status": "success",
            "data": {"user_count": user_count, "recent_events": recent_events},
        }


__all__ = ["AnalyticsService"]

