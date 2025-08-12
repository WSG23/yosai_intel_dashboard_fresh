from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, List, Sequence

import asyncpg

from infrastructure.security.query_builder import SecureQueryBuilder

from .validators.integrity_checker import IntegrityChecker

LOG = logging.getLogger(__name__)

# Only allow truncating approved tables to avoid SQL injection
APPROVED_TABLES = {
    "gateway_logs",
    "access_events",
    "analytics_results",
}


class MigrationStrategy(ABC):
    """Abstract base for service specific migration strategies."""

    def __init__(
        self,
        name: str,
        target_dsn: str,
        *,
        pool_factory: Callable[..., Awaitable[asyncpg.Pool]] | None = None,
    ) -> None:
        self.name = name
        self.target_dsn = target_dsn
        self.target_pool: asyncpg.Pool | None = None
        self.pool_factory = pool_factory or asyncpg.create_pool
        self.checker = IntegrityChecker()

    async def setup(self) -> None:
        self.target_pool = await self.pool_factory(dsn=self.target_dsn)

    @abstractmethod
    async def run(self, source_pool: asyncpg.Pool) -> AsyncIterator[int]:
        """Yield migrated row counts."""

    async def rollback(self) -> None:
        if self.target_pool is None:
            return
        async with self.target_pool.acquire() as conn:
            builder = SecureQueryBuilder(allowed_tables=APPROVED_TABLES)
            sql, _ = builder.build(
                "TRUNCATE TABLE %s CASCADE", self.name, logger=LOG
            )
            await conn.execute(sql)


class MigrationManager:
    """Coordinate database migration across multiple strategies."""

    def __init__(
        self,
        source_dsn: str,
        strategies: Sequence[MigrationStrategy],
        *,
        pool_factory: Callable[..., Awaitable[asyncpg.Pool]] | None = None,
    ) -> None:
        self.source_dsn = source_dsn
        self.strategies = list(strategies)
        self.source_pool: asyncpg.Pool | None = None
        self.tasks: List[asyncio.Task[Any]] = []
        self.progress: Dict[str, int] = {}
        self.failures: List[str] = []
        self.pool_factory = pool_factory or asyncpg.create_pool
        for strat in self.strategies:
            if (
                getattr(strat, "pool_factory", asyncpg.create_pool)
                is asyncpg.create_pool
            ):
                strat.pool_factory = self.pool_factory

    async def setup(self) -> None:
        self.source_pool = await self.pool_factory(dsn=self.source_dsn)
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
