from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Sequence

import asyncpg

from .validators.integrity_checker import IntegrityChecker

LOG = logging.getLogger(__name__)


class MigrationStrategy(ABC):
    """Abstract base for service specific migration strategies."""

    def __init__(self, name: str, target_dsn: str) -> None:
        self.name = name
        self.target_dsn = target_dsn
        self.target_pool: asyncpg.Pool | None = None
        self.checker = IntegrityChecker()

    async def setup(self) -> None:
        self.target_pool = await asyncpg.create_pool(dsn=self.target_dsn)

    @abstractmethod
    async def run(self, source_pool: asyncpg.Pool) -> AsyncIterator[int]:
        """Yield migrated row counts."""

    async def rollback(self) -> None:
        if self.target_pool is None:
            return
        async with self.target_pool.acquire() as conn:
            await conn.execute(f"TRUNCATE TABLE {self.name} CASCADE")


class MigrationManager:
    """Coordinate database migration across multiple strategies."""

    def __init__(self, source_dsn: str, strategies: Sequence[MigrationStrategy]):
        self.source_dsn = source_dsn
        self.strategies = list(strategies)
        self.source_pool: asyncpg.Pool | None = None
        self.tasks: List[asyncio.Task[Any]] = []
        self.progress: Dict[str, int] = {}
        self.failures: List[str] = []

    async def setup(self) -> None:
        self.source_pool = await asyncpg.create_pool(dsn=self.source_dsn)
        for strat in self.strategies:
            await strat.setup()

    async def migrate(self) -> None:
        await self.setup()
        assert self.source_pool is not None
        for strat in self.strategies:
            task = asyncio.create_task(self._run_strategy(strat))
            self.tasks.append(task)
        await asyncio.gather(*self.tasks)

    async def _run_strategy(self, strat: MigrationStrategy) -> None:
        assert self.source_pool is not None
        try:
            async for count in strat.run(self.source_pool):
                self.progress[strat.name] = self.progress.get(strat.name, 0) + count
        except Exception as exc:  # pragma: no cover - runtime failures
            LOG.exception("Migration %s failed: %s", strat.name, exc)
            self.failures.append(strat.name)
            await strat.rollback()

    async def rollback(self) -> None:
        for strat in self.strategies:
            await strat.rollback()

    async def status(self) -> Dict[str, Any]:
        return {"progress": self.progress, "failures": self.failures}


__all__ = ["MigrationManager", "MigrationStrategy"]
