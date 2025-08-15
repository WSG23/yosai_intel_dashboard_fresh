from __future__ import annotations

import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from src.services.database.analytics_service import AnalyticsService


def test_parameterized_queries_block_injection() -> None:
    """Ensure that unsafe string concatenation does not leak data."""

    async def _test() -> None:
        engine: AsyncEngine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"))
            await conn.execute(text("INSERT INTO users (name) VALUES ('alice'), ('bob')"))
            await conn.execute(
                text(
                    "CREATE TABLE access_events (event_type TEXT, status TEXT, timestamp TEXT)"
                )
            )

        service = AnalyticsService(async_sessionmaker(engine, expire_on_commit=False))

        payload = "alice' OR 1=1--"

        # Unsafe string concatenation would expose both rows
        async with engine.begin() as conn:
            unsafe_sql = f"SELECT name FROM users WHERE name = '{payload}'"
            rows = await conn.execute(text(unsafe_sql))
            assert len(rows.fetchall()) == 2  # injection succeeded

        # Parameter binding prevents the injection from matching anything
        async with engine.begin() as conn:
            safe_stmt = text("SELECT name FROM users WHERE name = :name")
            rows = await conn.execute(safe_stmt, {"name": payload})
            assert rows.fetchall() == []

        # Service uses parameterised queries internally and therefore works
        result = await service.get_analytics()
        assert result["status"] == "success"

    asyncio.run(_test())

