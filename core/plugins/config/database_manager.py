"""Enhanced database managers implementing the interface"""

import logging
from typing import Optional, Any, Dict

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import sqlite3
from .interfaces import IDatabaseManager, ConnectionResult

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

    def execute_query(self, query: str, params: Optional[Dict] = None) -> Any:
        """Execute mock query"""
        logger.debug(f"Mock query executed: {query}")
        return f"Mock result for: {query}"


class PostgreSQLDatabaseManager(IDatabaseManager):
    """PostgreSQL database manager"""

    def __init__(self, database_config):
        self.config = database_config
        self.connection = None

    def get_connection(self) -> ConnectionResult:
        """Get PostgreSQL connection"""
        if self.connection is not None:
            return ConnectionResult(
                success=True, connection=self.connection, connection_type="postgresql"
            )
        try:
            logger.info("Creating PostgreSQL connection")
            self.connection = psycopg2.connect(
                host=getattr(self.config, "host", "localhost"),
                port=getattr(self.config, "port", 5432),
                dbname=getattr(
                    self.config, "name", getattr(self.config, "database", "postgres")
                ),
                user=getattr(
                    self.config, "user", getattr(self.config, "username", "postgres")
                ),
                password=getattr(self.config, "password", ""),
                cursor_factory=RealDictCursor,
            )
            return ConnectionResult(
                success=True, connection=self.connection, connection_type="postgresql"
            )
        except Exception as e:
            logger.error("PostgreSQL connection failed: %s", e)
            return ConnectionResult(
                success=False,
                connection=None,
                error_message=str(e),
                connection_type="postgresql",
            )

    def test_connection(self) -> bool:
        """Test PostgreSQL connection"""
        result = self.get_connection()
        if not result.success or not result.connection:
            return False
        try:
            with result.connection.cursor() as cur:
                cur.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error("PostgreSQL test query failed: %s", e)
            return False

    def close_connection(self) -> None:
        """Close PostgreSQL connection"""
        if self.connection is not None:
            try:
                self.connection.close()
            except Exception:
                pass
        self.connection = None
        logger.info("PostgreSQL connection closed")

    def execute_query(self, query: str, params: Optional[Dict] = None) -> Any:
        """Execute PostgreSQL query and return pandas DataFrame or affected rows"""
        result = self.get_connection()
        if not result.success or not result.connection:
            raise ConnectionError(
                result.error_message or "PostgreSQL connection not available"
            )
        conn = result.connection
        try:
            with conn.cursor() as cur:
                cur.execute(query, params)
                if cur.description:
                    rows = cur.fetchall()
                    df = pd.DataFrame(rows)
                    return df
                conn.commit()
                return cur.rowcount
        except Exception as e:
            logger.error("PostgreSQL query failed: %s", e)
            conn.rollback()
            raise


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
            logger.error("SQLite connection failed: %s", e)
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
            logger.error("SQLite test query failed: %s", e)
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

    def execute_query(self, query: str, params: Optional[Dict] = None) -> Any:
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
                rows = [dict(row) for row in cur.fetchall()]
                df = pd.DataFrame(rows)
                return df
            conn.commit()
            return cur.rowcount
        except Exception as e:
            logger.error("SQLite query failed: %s", e)
            raise


__all__ = ["MockDatabaseManager", "PostgreSQLDatabaseManager", "SQLiteDatabaseManager"]
