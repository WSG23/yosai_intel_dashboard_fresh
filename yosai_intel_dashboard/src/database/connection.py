"""Database connection - compatible with existing codebase"""

from __future__ import annotations

from typing import Any, Iterable, Optional, Protocol

from opentelemetry import trace

from yosai_intel_dashboard.src.database.metrics import queries_total, query_errors_total
from yosai_intel_dashboard.src.database.types import DBRows
from yosai_intel_dashboard.src.database.utils import parse_connection_string
from yosai_intel_dashboard.src.infrastructure.config.database_manager import (
    DatabaseManager,
    MockConnection,
)

from .shard_resolver import ShardResolver


class DatabaseConnection(Protocol):
    """Database connection protocol"""

    def execute_query(self, query: str, params: Optional[tuple] = None) -> DBRows:
        """Execute SELECT query and return rows"""
        ...

    def execute_command(self, command: str, params: Optional[tuple] = None) -> None:
        """Execute INSERT/UPDATE/DELETE"""
        ...

    def prepare_statement(self, name: str, query: str) -> None:
        """Prepare ``query`` under ``name`` for later execution."""
        ...

    def execute_prepared(self, name: str, params: tuple) -> DBRows:
        """Execute a previously prepared statement."""

        ...

    def health_check(self) -> bool:
        """Check if database is accessible"""
        ...


def create_database_connection(
    table: Optional[str] = None,
    shard_key: Any = None,
    shard_resolver: Optional[ShardResolver] = None,
) -> DatabaseConnection:
    """Create database connection using :class:`DatabaseConnectionFactory`.

    Parameters
    ----------
    table:
        Optional name of the table being accessed.  When provided together with
        ``shard_key`` and ``shard_resolver`` the connection will be routed to
        the resolved shard.
    shard_key:
        Identifier used for sharding.  Any hashable value is accepted.
    shard_resolver:
        Resolver capable of mapping ``table`` and ``shard_key`` to a specific
        shard connection string.
    """

    from yosai_intel_dashboard.src.infrastructure.config import get_config

    config_manager = get_config()
    db_config = config_manager.get_database_config()

    # Determine shard specific configuration if applicable
    if table and shard_resolver and shard_key is not None:
        shard_url = shard_resolver.resolve(table, shard_key)
        if shard_url:
            db_config = db_config.model_copy(update={"url": shard_url})

    # Validate connection string before creating manager
    parse_connection_string(db_config.get_connection_string())
    # Create database manager with existing config
    db_manager = DatabaseManager(db_config)

    conn = db_manager.get_connection()

    tracer = trace.get_tracer("database")

    class InstrumentedConnection:
        def execute_query(self, query: str, params: Optional[tuple] = None) -> DBRows:
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

        def prepare_statement(self, name: str, query: str) -> None:
            with tracer.start_as_current_span("prepare_statement"):
                return conn.prepare_statement(name, query)

        def execute_prepared(self, name: str, params: tuple) -> DBRows:
            with tracer.start_as_current_span("execute_prepared"):
                queries_total.inc()
                try:
                    return conn.execute_prepared(name, params)

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
