from __future__ import annotations

"""Unified database connection factory with pooling and retries."""

import asyncio
import logging
import sqlite3
from pathlib import Path
from typing import Any, Optional

from database.types import DatabaseConnection

from ..config.connection_pool import DatabaseConnectionPool
from ..config.connection_retry import ConnectionRetryManager, RetryConfig
from ..config.database_exceptions import DatabaseError
from ..config.schema import DatabaseSettings
from ..config.unicode_processor import QueryUnicodeHandler

logger = logging.getLogger(__name__)


class MockConnection:
    """Simple in-memory mock connection used for testing."""

    def __init__(self) -> None:  # pragma: no cover - trivial
        self._connected = True

    def execute_query(self, query: str, params: Optional[tuple] = None) -> list:
        logger.debug("mock execute_query: %s", query)
        return [{"result": "mock"}]

    def execute_command(self, command: str, params: Optional[tuple] = None) -> None:
        logger.debug("mock execute_command: %s", command)

    def fetch_results(self, query: str, params: Optional[tuple] = None) -> list:
        return self.execute_query(query, params)

    def health_check(self) -> bool:
        return self._connected

    def close(self) -> None:
        self._connected = False


class SQLiteConnection:
    """SQLite connection wrapper implementing the ``DatabaseConnection`` protocol."""

    def __init__(self, config: DatabaseSettings) -> None:
        self._config = config
        db_file = Path(config.name)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(
            config.name, timeout=config.connection_timeout
        )
        self._connection.row_factory = sqlite3.Row

    def execute_query(self, query: str, params: Optional[tuple] = None) -> list:
        cursor = self._connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    def execute_command(self, command: str, params: Optional[tuple] = None) -> None:
        cursor = self._connection.cursor()
        if params:
            cursor.execute(command, params)
        else:
            cursor.execute(command)
        self._connection.commit()

    def fetch_results(self, query: str, params: Optional[tuple] = None) -> list:
        return self.execute_query(query, params)

    def health_check(self) -> bool:
        try:
            cursor = self._connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            return True
        except sqlite3.Error:
            return False

    def close(self) -> None:
        self._connection.close()


class PostgreSQLConnection:
    """PostgreSQL connection wrapper using ``psycopg2``."""

    def __init__(self, config: DatabaseSettings) -> None:
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise DatabaseError(
                "psycopg2 is required for PostgreSQL connections"
            ) from exc

        self._connection = psycopg2.connect(
            host=config.host,
            port=config.port,
            database=config.name,
            user=config.user,
            password=config.password,
            cursor_factory=RealDictCursor,
            connect_timeout=config.connection_timeout,
        )

    def execute_query(self, query: str, params: Optional[tuple] = None) -> list:
        with self._connection.cursor() as cursor:
            cursor.execute(query, params)
            return list(cursor.fetchall())

    def execute_command(self, command: str, params: Optional[tuple] = None) -> None:
        with self._connection.cursor() as cursor:
            cursor.execute(command, params)
            self._connection.commit()

    def fetch_results(self, query: str, params: Optional[tuple] = None) -> list:
        return self.execute_query(query, params)

    def health_check(self) -> bool:
        try:
            with self._connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            return True
        except Exception:
            return False

    def close(self) -> None:
        self._connection.close()


class PooledConnection:
    """Context manager wrapping a pooled connection."""

    def __init__(self, conn: DatabaseConnection, pool: DatabaseConnectionPool) -> None:
        self._conn = conn
        self._pool = pool

    def execute_query(self, query: str, params: Optional[tuple] = None) -> list:
        q = DatabaseConnectionFactory.encode_query(query)
        p = DatabaseConnectionFactory.encode_params(params)
        return self._conn.execute_query(q, p)

    def execute_command(self, command: str, params: Optional[tuple] = None) -> None:
        c = DatabaseConnectionFactory.encode_query(command)
        p = DatabaseConnectionFactory.encode_params(params)
        self._conn.execute_command(c, p)

    def fetch_results(self, query: str, params: Optional[tuple] = None) -> list:
        return self.execute_query(query, params)

    def health_check(self) -> bool:
        return self._conn.health_check()

    def __enter__(self) -> "PooledConnection":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self._pool.release_connection(self._conn)


class AsyncPooledConnection:
    """Async context manager for pooled connections."""

    def __init__(self, conn: DatabaseConnection, pool: DatabaseConnectionPool) -> None:
        self._conn = conn
        self._pool = pool

    async def execute_query(self, query: str, params: Optional[tuple] = None) -> list:
        q = DatabaseConnectionFactory.encode_query(query)
        p = DatabaseConnectionFactory.encode_params(params)
        return await asyncio.to_thread(self._conn.execute_query, q, p)

    async def execute_command(
        self, command: str, params: Optional[tuple] = None
    ) -> None:
        c = DatabaseConnectionFactory.encode_query(command)
        p = DatabaseConnectionFactory.encode_params(params)
        await asyncio.to_thread(self._conn.execute_command, c, p)

    async def fetch_results(self, query: str, params: Optional[tuple] = None) -> list:
        return await self.execute_query(query, params)

    async def health_check(self) -> bool:
        return await asyncio.to_thread(self._conn.health_check)

    async def __aenter__(self) -> "AsyncPooledConnection":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await asyncio.to_thread(self._pool.release_connection, self._conn)


class DatabaseConnectionFactory:
    """Factory to create database connections with pooling and retry."""

    def __init__(
        self, config: DatabaseSettings, retry_config: RetryConfig | None = None
    ) -> None:
        self._config = config
        self._retry = ConnectionRetryManager(retry_config or RetryConfig())
        self._pool = DatabaseConnectionPool(
            lambda: self._retry.run_with_retry(self._create_connection),
            config.initial_pool_size,
            config.max_pool_size,
            config.connection_timeout,
            config.shrink_timeout,
        )

    @staticmethod
    def encode_query(query: str) -> str:
        return QueryUnicodeHandler.handle_unicode_query(query)

    @staticmethod
    def encode_params(params: Any) -> Any:
        return QueryUnicodeHandler.handle_query_parameters(params)

    def _create_connection(self) -> DatabaseConnection:
        db_type = self._config.type.lower()
        if db_type in {"postgresql", "postgres"}:
            return PostgreSQLConnection(self._config)
        if db_type == "sqlite":
            return SQLiteConnection(self._config)
        return MockConnection()

    def get_connection(self) -> PooledConnection:
        conn = self._pool.get_connection()
        return PooledConnection(conn, self._pool)

    async def get_connection_async(self) -> AsyncPooledConnection:
        conn = await asyncio.to_thread(self._pool.get_connection)
        return AsyncPooledConnection(conn, self._pool)

    def health_check(self) -> bool:
        return self._pool.health_check()


__all__ = ["DatabaseConnectionFactory"]
