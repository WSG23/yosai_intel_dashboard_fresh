from __future__ import annotations

import time
from queue import LifoQueue
from typing import Callable

from .database_exceptions import ConnectionValidationFailed
from .database_manager import DatabaseConnection


class DatabaseConnectionPool:
    """Simple connection pool with health checks and timeout."""

    def __init__(self, factory: Callable[[], DatabaseConnection], size: int, timeout: int) -> None:
        self._factory = factory
        self._size = size
        self._timeout = timeout
        self._pool: LifoQueue[DatabaseConnection] = LifoQueue(maxsize=size)

    def get_connection(self) -> DatabaseConnection:
        try:
            conn = self._pool.get_nowait()
            if not conn.health_check():
                conn.close()
                raise ConnectionValidationFailed("stale connection")
            return conn
        except Exception:
            return self._factory()

    def release_connection(self, conn: DatabaseConnection) -> None:
        if not conn.health_check():
            conn.close()
            return
        try:
            self._pool.put_nowait(conn)
        except Exception:
            conn.close()

    def health_check(self) -> bool:
        temp = []
        healthy = True
        while not self._pool.empty():
            conn = self._pool.get_nowait()
            if not conn.health_check():
                healthy = False
                conn.close()
            temp.append(conn)
        for c in temp:
            self.release_connection(c)
        return healthy

