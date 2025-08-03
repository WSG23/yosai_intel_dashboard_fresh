"""Database connection - compatible with existing codebase"""

from typing import Optional, Protocol

from opentelemetry import trace

from yosai_intel_dashboard.src.infrastructure.config.database_manager import (
    DatabaseConnectionFactory,
)
from database.metrics import queries_total, query_errors_total
from database.types import DBRows


class DatabaseConnection(Protocol):
    """Database connection protocol"""

    def execute_query(self, query: str, params: Optional[tuple] = None) -> DBRows:
        """Execute SELECT query and return rows"""
        ...

    def execute_command(self, command: str, params: Optional[tuple] = None) -> None:
        """Execute INSERT/UPDATE/DELETE"""
        ...

    def health_check(self) -> bool:
        """Check if database is accessible"""
        ...


def create_database_connection() -> DatabaseConnection:
    """Create database connection using :class:`DatabaseConnectionFactory`."""
    from yosai_intel_dashboard.src.infrastructure.config import get_config

    config_manager = get_config()
    db_config = config_manager.get_database_config()

    factory = DatabaseConnectionFactory(db_config)
    conn = factory.create()

    tracer = trace.get_tracer("database")

    class InstrumentedConnection:
        def execute_query(
            self, query: str, params: Optional[tuple] = None
        ) -> DBRows:
            with tracer.start_as_current_span("execute_query"):
                queries_total.inc()
                try:
                    return conn.execute_query(query, params)
                except Exception:
                    query_errors_total.inc()
                    raise

        def execute_command(self, command: str, params: Optional[tuple] = None) -> None:
            with tracer.start_as_current_span("execute_command"):
                queries_total.inc()
                try:
                    return conn.execute_command(command, params)
                except Exception:
                    query_errors_total.inc()
                    raise

        def health_check(self) -> bool:
            return conn.health_check()

    return InstrumentedConnection()


# For compatibility with existing imports
__all__ = [
    "DatabaseConnection",
    "create_database_connection",
    "DatabaseConnectionFactory",
]
