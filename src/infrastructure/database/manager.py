"""Async database connection manager using asyncpg."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, List, Optional

import asyncpg

logger = logging.getLogger(__name__)


@dataclass
class DatabaseConfig:
    host: str
    port: int
    database: str
    username: str
    password: str
    min_connections: int
    max_connections: int
    timeout: float


class DatabaseManager:
    """Manage asyncpg connection pool and operations."""

    def __init__(self, config: DatabaseConfig) -> None:
        self._config = config
        self._pool: Optional[asyncpg.Pool] = None
        self._is_healthy = False

    @property
    def is_healthy(self) -> bool:
        """Return current health status of the pool."""

        return self._is_healthy

    async def initialize(self) -> None:
        """Create the asyncpg connection pool."""

        try:
            self._pool = await asyncpg.create_pool(
                host=self._config.host,
                port=self._config.port,
                database=self._config.database,
                user=self._config.username,
                password=self._config.password,
                min_size=self._config.min_connections,
                max_size=self._config.max_connections,
                timeout=self._config.timeout,
            )
            self._is_healthy = True
        except Exception as exc:  # pragma: no cover - unexpected
            self._is_healthy = False
            logger.exception("Failed to initialize database pool")
            raise RuntimeError("Failed to initialize database pool") from exc

    async def close(self) -> None:
        """Close the pool if initialized."""

        if self._pool is not None:
            await self._pool.close()
            self._pool = None
        self._is_healthy = False

    @asynccontextmanager
    async def get_connection(self) -> AsyncIterator[asyncpg.Connection]:
        """Acquire a connection from the pool."""

        if self._pool is None:
            message = "Database pool has not been initialized"
            logger.error(message)
            raise RuntimeError(message)

        try:
            async with self._pool.acquire() as connection:
                yield connection
        except Exception as exc:
            self._is_healthy = False
            logger.exception("Failed to acquire database connection")
            raise RuntimeError("Failed to acquire database connection") from exc

    async def execute_query(self, query: str, *args) -> List[asyncpg.Record]:
        """Run a SELECT query and return records."""

        try:
            async with self.get_connection() as conn:
                return await conn.fetch(query, *args)
        except Exception as exc:
            self._is_healthy = False
            logger.exception("Query execution failed: %s", query)
            raise RuntimeError(f"Query execution failed: {query}") from exc

    async def execute_command(self, command: str, *args) -> str:
        """Run a data modification command and return status."""

        try:
            async with self.get_connection() as conn:
                return await conn.execute(command, *args)
        except Exception as exc:
            self._is_healthy = False
            logger.exception("Command execution failed: %s", command)
            raise RuntimeError(f"Command execution failed: {command}") from exc

    async def health_check(self) -> bool:
        """Run a simple query to verify connectivity."""

        try:
            await self.execute_query("SELECT 1")
            self._is_healthy = True
        except Exception:
            logger.exception("Health check failed")
            self._is_healthy = False
        return self._is_healthy
