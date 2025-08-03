from __future__ import annotations

"""Type protocol definitions for database connections.

The :class:`DatabaseConnection` protocol describes the minimal interface
expected by the connection pools and helpers in this package.
"""

from typing import Any, Dict, List, Optional, Protocol


# ---------------------------------------------------------------------------
# Result type aliases
# ---------------------------------------------------------------------------
DBRow = Dict[str, Any]
DBRows = List[DBRow]


class DatabaseConnection(Protocol):
    """Protocol for database connections"""

    def execute_query(self, query: str, params: Optional[tuple] = None) -> DBRows:
        """Execute a query and return results"""
        ...

    def execute_command(self, command: str, params: Optional[tuple] = None) -> None:
        """Execute a command (INSERT, UPDATE, DELETE)"""
        ...

    def prepare_statement(self, name: str, query: str) -> None:
        """Prepare ``query`` under ``name`` for later execution."""
        ...

    def execute_prepared(self, name: str, params: tuple) -> DBRows:
        """Execute a previously prepared statement."""
        ...

    def health_check(self) -> bool:
        """Verify database connectivity"""
        ...


__all__ = ["DBRow", "DBRows", "DatabaseConnection"]
