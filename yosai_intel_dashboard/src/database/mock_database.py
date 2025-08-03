from __future__ import annotations

"""In-memory mock implementation of :class:`ConnectionProtocol`.

This helper provides a lightweight stand-in for a real database connection.
It implements the full :class:`ConnectionProtocol` interface while returning
stubbed data.  The mock is intended for unit tests where a database is
unnecessary or unavailable.  It does not perform any real SQL parsing or
persistence and should never be used in production code.
"""

from typing import Any, List, Optional

from .protocols import ConnectionProtocol


class MockDatabase(ConnectionProtocol):
    """Simple mock database used for tests."""

    def __init__(self) -> None:
        self.connected = True
        self.queries: List[tuple[str, Optional[tuple]]] = []
        self.commands: List[tuple[str, Optional[tuple]]] = []

    def execute_query(self, query: str, params: Optional[tuple] = None) -> list[dict[str, Any]]:
        """Record query and return empty result set."""
        self.queries.append((query, params))
        return []

    def execute_command(self, command: str, params: Optional[tuple] = None) -> int:
        """Record command and report zero affected rows."""
        self.commands.append((command, params))
        return 0

    def fetch_results(self, query: str, params: Optional[tuple] = None) -> list[dict[str, Any]]:
        """Return stub results for ``query``.

        This method simply proxies to :meth:`execute_query` but provides a
        clearer API for callers that only need to retrieve data.
        """
        return self.execute_query(query, params)

    def health_check(self) -> bool:
        """Indicate whether the mock connection is considered healthy."""
        return self.connected

    def close(self) -> None:
        """Mark the mock connection as closed."""
        self.connected = False


__all__ = ["MockDatabase"]
