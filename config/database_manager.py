#!/usr/bin/env python3
from __future__ import annotations

"""
Database Manager - Fixed imports for streamlined architecture
"""
import logging
import sqlite3
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

from core.unicode import UnicodeSQLProcessor
from database.types import DatabaseConnection
from database.query_optimizer import DatabaseQueryOptimizer

if TYPE_CHECKING:  # pragma: no cover - for type hints
    from .connection_pool import DatabaseConnectionPool

from .base import DatabaseConfig
from .database_exceptions import ConnectionValidationFailed, DatabaseError
from .protocols import (
    ConnectionRetryManagerProtocol,
    RetryConfigProtocol,
)

logger = logging.getLogger(__name__)


class MockConnection:
    """Mock database connection for testing"""

    def __init__(self):
        self._connected = True
        logger.info("Mock database connection created")

    def execute_query(self, query: str, params: Optional[tuple] = None) -> list:
        """Execute mock query"""
        logger.debug(f"Mock query: {query}")
        return [{"id": 1, "result": "mock_data"}]

    def execute_command(self, command: str, params: Optional[tuple] = None) -> None:
        """Execute mock command"""
        logger.debug(f"Mock command: {command}")

    def health_check(self) -> bool:
        """Mock health check"""
        return self._connected

    def close(self) -> None:
        """Close mock connection"""
        self._connected = False
        logger.info("Mock database connection closed")


class SQLiteConnection:
    """SQLite database connection"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.db_path = config.name
        self._connection: Optional[sqlite3.Connection] = None
        self._connect()

    def _connect(self) -> None:
        """Create SQLite connection"""
        try:
            # Ensure directory exists
            db_file = Path(self.db_path)
            db_file.parent.mkdir(parents=True, exist_ok=True)

            self._connection = sqlite3.connect(
                self.db_path, timeout=self.config.connection_timeout
            )
            self._connection.row_factory = sqlite3.Row  # Enable dict-like access
            logger.info(f"SQLite connection created: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to SQLite: {e}")
            raise DatabaseError(f"SQLite connection failed: {e}") from e

    def execute_query(self, query: str, params: Optional[tuple] = None) -> list:
        """Execute SQLite query"""
        if not self._connection:
            raise DatabaseError("No database connection")

        try:
            cursor = self._connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"SQLite query error: {e}")
            raise DatabaseError(f"Query failed: {e}") from e

    def execute_command(self, command: str, params: Optional[tuple] = None) -> None:
        """Execute SQLite command"""
        if not self._connection:
            raise DatabaseError("No database connection")

        try:
            cursor = self._connection.cursor()
            if params:
                cursor.execute(command, params)
            else:
                cursor.execute(command)

            self._connection.commit()
        except sqlite3.Error as e:
            logger.error(f"SQLite command error: {e}")
            raise DatabaseError(f"Command failed: {e}") from e

    def health_check(self) -> bool:
        """Check SQLite connection health"""
        try:
            if not self._connection:
                return False

            cursor = self._connection.cursor()
            cursor.execute("SELECT 1")
            return True
        except sqlite3.Error:
            return False

    def close(self) -> None:
        """Close SQLite connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("SQLite connection closed")


class PostgreSQLConnection:
    """PostgreSQL database connection (requires psycopg2)"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._connection = None
        self._connect()

    def _connect(self) -> None:
        """Create PostgreSQL connection"""
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
        except ImportError as exc:
            raise DatabaseError(
                "psycopg2 not installed - cannot connect to PostgreSQL"
            ) from exc

        try:
            self._connection = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.name,
                user=self.config.user,
                password=self.config.password,
                cursor_factory=RealDictCursor,
                connect_timeout=self.config.connection_timeout,
            )
            logger.info(
                f"PostgreSQL connection created: {self.config.host}:{self.config.port}"
            )
            with self._connection.cursor() as cursor:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS timescaledb;")
                self._connection.commit()
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to PostgreSQL: {e}")
            raise DatabaseError(f"PostgreSQL connection failed: {e}") from e

    def execute_query(self, query: str, params: Optional[tuple] = None) -> list:
        """Execute PostgreSQL query"""
        if not self._connection:
            raise DatabaseError("No database connection")

        try:
            with self._connection.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except psycopg2.Error as e:
            logger.error(f"PostgreSQL query error: {e}")
            raise DatabaseError(f"Query failed: {e}") from e

    def execute_command(self, command: str, params: Optional[tuple] = None) -> None:
        """Execute PostgreSQL command"""
        if not self._connection:
            raise DatabaseError("No database connection")

        try:
            with self._connection.cursor() as cursor:
                if params:
                    cursor.execute(command, params)
                else:
                    cursor.execute(command)

            self._connection.commit()
        except psycopg2.Error as e:
            logger.error(f"PostgreSQL command error: {e}")
            self._connection.rollback()
            raise DatabaseError(f"Command failed: {e}") from e

    def health_check(self) -> bool:
        """Check PostgreSQL connection health"""
        try:
            if not self._connection:
                return False

            with self._connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except psycopg2.Error:
            return False

    def close(self) -> None:
        """Close PostgreSQL connection"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("PostgreSQL connection closed")


class DatabaseManager:
    """Database manager factory"""

    def __init__(self, config: DatabaseConfig):
        self.config = config
        self._connection: Optional[DatabaseConnection] = None

    def get_connection(self) -> DatabaseConnection:
        """Get database connection"""
        if self._connection is None:
            self._connection = self._create_connection()
        return self._connection

    def _create_connection(self) -> DatabaseConnection:
        """Create appropriate database connection"""
        db_type = self.config.type.lower()

        if db_type == "mock":
            return MockConnection()

        elif db_type == "sqlite":
            return SQLiteConnection(self.config)

        elif db_type in ["postgresql", "postgres"]:
            return PostgreSQLConnection(self.config)

        else:
            logger.warning(f"Unknown database type: {db_type}, using mock")
            return MockConnection()

    def health_check(self) -> bool:
        """Check database health"""
        try:
            connection = self.get_connection()
            return connection.health_check()
        except DatabaseError:
            return False

    def close(self) -> None:
        """Close database connection"""
        if self._connection and hasattr(self._connection, "close"):
            self._connection.close()
            self._connection = None


class ThreadSafeDatabaseManager(DatabaseManager):
    """DatabaseManager with thread-safe lazy pool creation."""

    def __init__(self, config: DatabaseConfig) -> None:
        super().__init__(config)
        self._lock = threading.RLock()
        self._pool: Optional[Any] = None

    def _create_pool(self) -> DatabaseConnectionPool:
        if getattr(self.config, "use_intelligent_pool", False):
            from database.intelligent_connection_pool import IntelligentConnectionPool

            pool_cls = IntelligentConnectionPool
        else:
            from .connection_pool import DatabaseConnectionPool

            pool_cls = DatabaseConnectionPool

        return pool_cls(
            self._create_connection,
            getattr(self.config, "initial_pool_size", 1),
            getattr(self.config, "max_pool_size", 1),
            getattr(self.config, "connection_timeout", 30),
            getattr(self.config, "shrink_timeout", 60),
        )

    def get_connection(self) -> DatabaseConnection:  # type: ignore[override]
        with self._lock:
            if self._pool is None:
                self._pool = self._create_pool()
            return self._pool.get_connection()

    def release_connection(self, conn: DatabaseConnection) -> None:
        with self._lock:
            if self._pool:
                self._pool.release_connection(conn)


# Factory function
def create_database_manager(config: DatabaseConfig) -> DatabaseManager:
    """Create database manager from config"""
    return DatabaseManager(config)


# Export main classes
__all__ = [
    "DatabaseConfig",
    "DatabaseConnection",
    "MockConnection",
    "SQLiteConnection",
    "PostgreSQLConnection",
    "DatabaseManager",
    "ThreadSafeDatabaseManager",
    "DatabaseError",
    "create_database_manager",
    "EnhancedPostgreSQLManager",
]


class EnhancedPostgreSQLManager(DatabaseManager):
    """PostgreSQL manager with retry, pooling and Unicode safety."""

    def __init__(
        self,
        config: DatabaseConfig,
        retry_config: RetryConfigProtocol | None = None,
    ) -> None:
        super().__init__(config)
        from database.connection_pool import EnhancedConnectionPool
        from database.performance_analyzer import DatabasePerformanceAnalyzer

        from .connection_retry import ConnectionRetryManager, RetryConfig

        self.retry_manager: ConnectionRetryManagerProtocol = ConnectionRetryManager(
            retry_config or RetryConfig()
        )
        self.performance_analyzer = DatabasePerformanceAnalyzer()

        self.pool = EnhancedConnectionPool(
            self._create_connection,
            self.config.initial_pool_size,
            self.config.max_pool_size,
            self.config.connection_timeout,
            self.config.shrink_timeout,
        )

    def execute_query_with_retry(self, query: str, params: Optional[Dict] = None):
        encoded_query = UnicodeSQLProcessor.encode_query(query)
        optimized_query = self.optimizer.optimize_query(encoded_query)

        def _encode_params(value: Any) -> Any:
            if isinstance(value, str):
                return UnicodeSQLProcessor.encode_query(value)
            if isinstance(value, dict):
                return {k: _encode_params(v) for k, v in value.items()}
            if isinstance(value, (list, tuple, set)):
                return type(value)(_encode_params(v) for v in value)
            return value

        encoded_params = _encode_params(params)

        def run():
            conn = self.pool.get_connection()
            try:
                start = time.perf_counter()
                result = conn.execute_query(encoded_query, encoded_params)
                elapsed = time.perf_counter() - start
                self.performance_analyzer.analyze_query_performance(
                    encoded_query, elapsed
                )
                return result

            finally:
                self.pool.release_connection(conn)

        return self.retry_manager.run_with_retry(run)

    def health_check_with_retry(self) -> bool:
        def run():
            conn = self.pool.get_connection()
            try:
                if not conn.health_check():
                    raise ConnectionValidationFailed("health check failed")
                return True
            finally:
                self.pool.release_connection(conn)

        return self.retry_manager.run_with_retry(run)
