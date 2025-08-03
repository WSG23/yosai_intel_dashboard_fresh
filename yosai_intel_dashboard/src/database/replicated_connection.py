from __future__ import annotations

"""Connection wrapper that routes read-only queries to replicas."""

from itertools import cycle
from typing import Iterable, Optional

from .types import DBRows, DatabaseConnection


class ReplicatedDatabaseConnection:
    """Route reads to replica connections while writes go to primary."""

    def __init__(
        self,
        primary: DatabaseConnection,
        replicas: Iterable[DatabaseConnection],
    ) -> None:
        self._primary = primary
        self._replicas = list(replicas)
        self._cycle = cycle(self._replicas) if self._replicas else None

    def _choose_replica(self) -> DatabaseConnection:
        if self._cycle is None:
            return self._primary
        return next(self._cycle)

    # -- read operations -------------------------------------------------
    def execute_query(self, query: str, params: Optional[tuple] = None) -> DBRows:
        return self._choose_replica().execute_query(query, params)

    def execute_prepared(self, name: str, params: tuple) -> DBRows:
        return self._choose_replica().execute_prepared(name, params)

    # -- write operations ------------------------------------------------
    def execute_command(self, command: str, params: Optional[tuple] = None) -> None:
        self._primary.execute_command(command, params)

    # -- shared operations -----------------------------------------------
    def prepare_statement(self, name: str, query: str) -> None:
        self._primary.prepare_statement(name, query)
        for replica in self._replicas:
            replica.prepare_statement(name, query)

    def health_check(self) -> bool:
        if not self._primary.health_check():
            return False
        return all(replica.health_check() for replica in self._replicas)

    def close(self) -> None:
        if hasattr(self._primary, "close"):
            self._primary.close()
        for replica in self._replicas:
            if hasattr(replica, "close"):
                replica.close()


__all__ = ["ReplicatedDatabaseConnection"]
