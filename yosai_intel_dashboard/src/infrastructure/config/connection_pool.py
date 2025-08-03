from __future__ import annotations

import threading
import time
from typing import Callable, List, Tuple

from database.types import DatabaseConnection

from ..monitoring.prometheus.connection_pool import (
    db_pool_active_connections,
    db_pool_current_size,
    db_pool_wait_seconds,
)


class DatabaseConnectionPool:
    """Connection pool that can grow and shrink based on usage."""

    def __init__(
        self,
        factory: Callable[[], DatabaseConnection],
        initial_size: int,
        max_size: int,
        timeout: int,
        shrink_timeout: int,
        threshold: float = 0.8,
    ) -> None:
        self._lock = threading.RLock()
        self._factory = factory
        self._initial_size = initial_size
        self._max_pool_size = max(max_size, initial_size)
        self._max_size = initial_size
        self._timeout = timeout
        self._shrink_timeout = shrink_timeout
        self._threshold = threshold

        self._pool: List[Tuple[DatabaseConnection, float]] = []
        self._active = 0

        for _ in range(initial_size):
            conn = self._factory()
            self._pool.append((conn, time.time()))
            self._active += 1

        self._update_metrics()

    def _update_metrics(self) -> None:
        """Update Prometheus gauges to reflect pool state."""
        db_pool_current_size.set(self._max_size)
        db_pool_active_connections.set(self._active - len(self._pool))

    def _maybe_expand(self) -> None:
        with self._lock:
            if self._max_size == 0:
                return
            usage = (self._active - len(self._pool)) / self._max_size
            if usage >= self._threshold and self._max_size < self._max_pool_size:
                self._max_size = min(self._max_size * 2, self._max_pool_size)
                self._update_metrics()

    def _shrink_idle_connections(self) -> None:
        with self._lock:
            now = time.time()
            new_pool: List[Tuple[DatabaseConnection, float]] = []
            for conn, ts in self._pool:
                if (
                    now - ts > self._shrink_timeout
                    and self._max_size > self._initial_size
                ):
                    conn.close()
                    self._active -= 1
                    self._max_size -= 1
                else:
                    new_pool.append((conn, ts))
            self._pool = new_pool
            self._update_metrics()

    def get_connection(self) -> DatabaseConnection:
        start = time.time()
        deadline = start + self._timeout
        while True:
            with self._lock:
                self._shrink_idle_connections()
                # Check if pool usage is high before handing out a connection
                self._maybe_expand()

                if self._pool:
                    conn, _ = self._pool.pop()
                    if not conn.health_check():
                        conn.close()
                        self._active -= 1
                        self._update_metrics()
                        continue
                    self._update_metrics()
                    db_pool_wait_seconds.observe(time.time() - start)
                    return conn

                if self._active < self._max_size:
                    conn = self._factory()
                    self._active += 1
                    self._update_metrics()
                    db_pool_wait_seconds.observe(time.time() - start)
                    return conn

            if time.time() >= deadline:
                db_pool_wait_seconds.observe(time.time() - start)
                raise TimeoutError("No available connection in pool")

            time.sleep(0.05)

    def release_connection(self, conn: DatabaseConnection) -> None:
        with self._lock:
            self._shrink_idle_connections()
            if not conn.health_check():
                conn.close()
                self._active -= 1
                self._update_metrics()
                return

            if len(self._pool) >= self._max_size:
                conn.close()
                self._active -= 1
            else:
                self._pool.append((conn, time.time()))
            self._update_metrics()

    def health_check(self) -> bool:
        with self._lock:
            temp: List[Tuple[DatabaseConnection, float]] = []
            healthy = True
            while self._pool:
                conn, ts = self._pool.pop()
                if not conn.health_check():
                    healthy = False
                    conn.close()
                    self._active -= 1
                    if self._max_size > self._initial_size:
                        self._max_size -= 1
                else:
                    temp.append((conn, ts))
            for item in temp:
                self.release_connection(item[0])
            self._update_metrics()
            return healthy
