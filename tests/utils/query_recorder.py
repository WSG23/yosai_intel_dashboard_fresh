from __future__ import annotations

from typing import Any, Optional


class QueryRecordingConnection:
    """Wrap a database connection and record executed statements."""

    def __init__(self, base: Any) -> None:
        self._base = base
        self.statements: list[str] = []

    def execute_query(self, query: str, params: Optional[tuple] = None):
        self.statements.append(query)
        return self._base.execute_query(query, params)

    def execute_command(self, command: str, params: Optional[tuple] = None):
        self.statements.append(command)
        return self._base.execute_command(command, params)

    def __getattr__(self, item: str) -> Any:
        return getattr(self._base, item)


__all__ = ["QueryRecordingConnection"]
