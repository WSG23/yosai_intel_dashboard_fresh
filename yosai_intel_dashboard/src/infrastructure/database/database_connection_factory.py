from __future__ import annotations

"""Unified database connection factory with pooling and retries."""

import asyncio
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional, Set

from yosai_intel_dashboard.src.database.types import DatabaseConnection

from ..config.connection_pool import DatabaseConnectionPool
from ..config.connection_retry import ConnectionRetryManager, RetryConfig
from ..config.database_exceptions import DatabaseError
from ..config.schema import DatabaseSettings
from ..config.unicode_processor import QueryUnicodeHandler
from .secure_query import log_sanitized_query

logger = logging.getLogger(__name__)


class MockConnection:
    """Simple in-memory mock connection used for testing."""

    def __init__(self) -> None:  # pragma: no cover - trivial
        self._connected = True
        self._prepared: Dict[str, str] = {}

    def execute_query(self, query: str, params: Optional[tuple] = None) -> list:
        logger.debug("mock execute_query: %s", query)
        return [{"result": "mock"}]

    def execute_command(self, command: str, params: Optional[tuple] = None) -> None:
        logger.debug("mock execute_command: %s", command)

    def fetch_results(self, query: str, params: Optional[tuple] = None) -> list:
        return self.execute_query(query, params)

    def prepare_statement(self, name: str, query: str) -> None:
        self._prepared[name] = query

    def execute_prepared(self, name: str, params: tuple) -> list:
        query = self._prepared.get(name)
        if query is None:
            raise KeyError(f"Statement {name} has not been prepared")
        if query.lstrip().lower().startswith("select"):
            return self.execute_query(query, params)
        self.execute_command(query, params)
        return []

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
        self._prepared: Dict[str, tuple[str, sqlite3.Cursor]] = {}

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

    def prepare_statement(self, name: str, query: str) -> None:
        if name not in self._prepared:
            cursor = self._connection.cursor()
            self._prepared[name] = (query, cursor)

    def execute_prepared(self, name: str, params: tuple) -> list:
        query, cursor = self._prepared[name]
        cursor.execute(query, params)
        if cursor.description:
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        self._connection.commit()
        return []

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
            from psycopg2 import sql
            from psycopg2.extras import RealDictCursor
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise DatabaseError(
                "psycopg2 is required for PostgreSQL connections"
            ) from exc

        self._sql = sql
        self._connection = psycopg2.connect(
            host=config.host,
            port=config.port,
            database=config.name,
            user=config.user,
            password=config.password,
            cursor_factory=RealDictCursor,
            connect_timeout=config.connection_timeout,
        )
        self._prepared: Set[str] = set()

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

    def prepare_statement(self, name: str, query: str) -> None:
        if name in self._prepared:
            return
        sql_mod = self._sql
        with self._connection.cursor() as cursor:
            stmt = sql_mod.SQL("PREPARE {name} AS {query}").format(
                name=sql_mod.Identifier(name),
                query=sql_mod.SQL(query),
            )
            cursor.execute(stmt)
        self._prepared.add(name)

    def execute_prepared(self, name: str, params: tuple) -> list:
        sql_mod = self._sql
        with self._connection.cursor() as cursor:
            if params:
                placeholders = sql_mod.SQL(", ").join(
                    sql_mod.Placeholder() for _ in params
                )
                stmt = sql_mod.SQL("EXECUTE {name} ({params})").format(
                    name=sql_mod.Identifier(name),
                    params=placeholders,
                )
                cursor.execute(stmt, params)
            else:
                stmt = sql_mod.SQL("EXECUTE {name}").format(
                    name=sql_mod.Identifier(name)
                )
                cursor.execute(stmt)

            if cursor.description:
                return list(cursor.fetchall())
            self._connection.commit()
            return []

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
        log_sanitized_query(logger, q, p)
        return self._conn.execute_query(q, p)

    def execute_command(self, command: str, params: Optional[tuple] = None) -> None:
        c = DatabaseConnectionFactory.encode_query(command)
        p = DatabaseConnectionFactory.encode_params(params)
        log_sanitized_query(logger, c, p)
        self._conn.execute_command(c, p)

    def fetch_results(self, query: str, params: Optional[tuple] = None) -> list:
        return self.execute_query(query, params)

    def prepare_statement(self, name: str, query: str) -> None:
        q = DatabaseConnectionFactory.encode_query(query)
        self._conn.prepare_statement(name, q)

    def execute_prepared(self, name: str, params: tuple) -> list:
        p = DatabaseConnectionFactory.encode_params(params)
        return self._conn.execute_prepared(name, p)

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
        log_sanitized_query(logger, q, p)
        return await asyncio.to_thread(self._conn.execute_query, q, p)

    async def execute_command(
        self, command: str, params: Optional[tuple] = None
    ) -> None:
        c = DatabaseConnectionFactory.encode_query(command)
        p = DatabaseConnectionFactory.encode_params(params)
        log_sanitized_query(logger, c, p)
        await asyncio.to_thread(self._conn.execute_command, c, p)

    async def fetch_results(self, query: str, params: Optional[tuple] = None) -> list:
        return await self.execute_query(query, params)

    async def prepare_statement(self, name: str, query: str) -> None:
        q = DatabaseConnectionFactory.encode_query(query)
        await asyncio.to_thread(self._conn.prepare_statement, name, q)

    async def execute_prepared(self, name: str, params: tuple) -> list:
        p = DatabaseConnectionFactory.encode_params(params)
        return await asyncio.to_thread(self._conn.execute_prepared, name, p)

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
