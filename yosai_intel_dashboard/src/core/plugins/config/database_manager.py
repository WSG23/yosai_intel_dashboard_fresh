"""Enhanced database managers implementing the interface"""

import logging
import sqlite3
from typing import Any, Dict, Optional

from yosai_intel_dashboard.src.database.types import DBRows
from yosai_intel_dashboard.src.infrastructure.config.constants import (
    DEFAULT_DB_HOST,
    DEFAULT_DB_PORT,
)

from .async_database_manager import AsyncPostgreSQLManager
from .interfaces import ConnectionResult, IDatabaseManager

logger = logging.getLogger(__name__)


class MockDatabaseManager(IDatabaseManager):
    """Mock database manager for testing and development"""

    def __init__(self, database_config):
        self.config = database_config
        self._connected = False
        self._mock_data = {}

    def get_connection(self) -> ConnectionResult:
        """Get mock database connection"""
        self._connected = True
        return ConnectionResult(
            success=True, connection="mock_connection", connection_type="mock"
        )

    def test_connection(self) -> bool:
        """Test mock connection"""
        return True

    def close_connection(self) -> None:
        """Close mock connection"""
        self._connected = False
        logger.info("Mock database connection closed")

    def execute_query(self, query: str, params: Optional[Dict] = None) -> DBRows:
        """Execute mock query"""
        logger.debug(f"Mock query executed: {query}")
        return [{"result": f"Mock result for: {query}"}]


class SQLiteDatabaseManager(IDatabaseManager):
    """SQLite database manager"""

    def __init__(self, database_config):
        self.config = database_config
        self.connection = None

    def get_connection(self) -> ConnectionResult:
        """Get SQLite connection"""
        if self.connection is not None:
            return ConnectionResult(
                success=True, connection=self.connection, connection_type="sqlite"
            )
        try:
            logger.info("Creating SQLite connection")
            db_path = getattr(
                self.config, "database", getattr(self.config, "name", ":memory:")
            )
            self.connection = sqlite3.connect(db_path)
            self.connection.row_factory = sqlite3.Row
            return ConnectionResult(
                success=True, connection=self.connection, connection_type="sqlite"
            )
        except Exception as e:
            logger.error(f"SQLite connection failed: {e}")
            return ConnectionResult(
                success=False,
                connection=None,
                error_message=str(e),
                connection_type="sqlite",
            )

    def test_connection(self) -> bool:
        """Test SQLite connection"""
        result = self.get_connection()
        if not result.success or not result.connection:
            return False
        try:
            cur = result.connection.cursor()
            cur.execute("SELECT 1")
            cur.close()
            return True
        except Exception as e:
            logger.error(f"SQLite test query failed: {e}")
            return False

    def close_connection(self) -> None:
        """Close SQLite connection"""
        if self.connection is not None:
            try:
                self.connection.close()
            except Exception:
                pass
        self.connection = None
        logger.info("SQLite connection closed")

    def execute_query(self, query: str, params: Optional[Dict] = None) -> DBRows:
        """Execute SQLite query"""
        result = self.get_connection()
        if not result.success or not result.connection:
            raise ConnectionError(
                result.error_message or "SQLite connection not available"
            )
        conn = result.connection
        try:
            cur = conn.cursor()
            cur.execute(query, params or [])
            if cur.description:
                return [dict(row) for row in cur.fetchall()]
            conn.commit()
            return []
        except Exception as e:
            logger.error(f"SQLite query failed: {e}")
            raise


__all__ = [
    "MockDatabaseManager",
    "SQLiteDatabaseManager",
    "AsyncPostgreSQLManager",
]
