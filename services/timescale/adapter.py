from __future__ import annotations

from typing import Any, List, Dict

from .manager import TimescaleDBManager
from services.analytics_microservice import queries


class TimescaleAdapter:
    """High level helper for common TimescaleDB analytics queries."""

    def __init__(self, manager: TimescaleDBManager | None = None) -> None:
        self.manager = manager or TimescaleDBManager()

    async def hourly_event_counts(self, days: int) -> List[Dict[str, Any]]:
        await self.manager.connect()
        assert self.manager.pool is not None
        return await queries.hourly_event_counts(self.manager.pool, days)

    async def top_doors(self, days: int, limit: int = 5) -> List[Dict[str, Any]]:
        await self.manager.connect()
        assert self.manager.pool is not None
        return await queries.top_doors(self.manager.pool, days, limit)
