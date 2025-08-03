from __future__ import annotations

"""Protocol definitions for lightweight database connections."""

from typing import Any, Optional, Protocol, runtime_checkable


@runtime_checkable
class ConnectionProtocol(Protocol):
    """Minimal protocol required of database-like connections."""

    def execute_query(self, query: str, params: Optional[tuple] = None) -> Any:
        """Execute ``query`` and return results."""
        ...

    def execute_command(self, command: str, params: Optional[tuple] = None) -> Any:
        """Execute modification ``command`` and return an optional result."""
        ...

    def fetch_results(self, query: str, params: Optional[tuple] = None) -> Any:
        """Return results for ``query`` without modifying state."""
        ...

    def health_check(self) -> bool:
        """Return ``True`` if the connection is healthy."""
        ...

    def close(self) -> None:
        """Close the connection."""
        ...


__all__ = ["ConnectionProtocol"]
