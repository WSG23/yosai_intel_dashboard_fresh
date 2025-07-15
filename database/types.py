from __future__ import annotations

from typing import Any, Optional, Protocol


class DatabaseConnection(Protocol):
    """Protocol for database connections"""

    def execute_query(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute a query and return results"""
        ...

    def execute_command(self, command: str, params: Optional[tuple] = None) -> None:
        """Execute a command (INSERT, UPDATE, DELETE)"""
        ...

    def health_check(self) -> bool:
        """Verify database connectivity"""
        ...


__all__ = ["DatabaseConnection"]
