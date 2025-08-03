from __future__ import annotations

import logging
import threading
import time
from typing import Callable, List, Tuple

from database.types import DatabaseConnection


logger = logging.getLogger(__name__)


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

    def _maybe_expand(self) -> None:
        with self._lock:
            if self._max_size == 0:
                return
            usage = (self._active - len(self._pool)) / self._max_size
            if usage >= self._threshold and self._max_size < self._max_pool_size:
                new_size = min(self._max_size * 2, self._max_pool_size)
                logger.warning(
                    "Expanding connection pool to %d due to usage %.2f",
                    new_size,
                    usage,
                )
                self._max_size = new_size

    def _shrink_idle_connections(self) -> None:
        with self._lock:
            now = time.time()
            new_pool: List[Tuple[DatabaseConnection, float]] = []
            for conn, ts in self._pool:
                if (
                    now - ts > self._shrink_timeout
                    and self._max_size > self._initial_size
                ):
                    logger.warning(
                        "Closing idle connection after %.2fs", now - ts
                    )
                    conn.close()
                    self._active -= 1
                    self._max_size -= 1
                else:
                    new_pool.append((conn, ts))
            self._pool = new_pool

    def get_connection(self) -> DatabaseConnection:
        deadline = time.time() + self._timeout
        while True:
            with self._lock:
                self._shrink_idle_connections()
                # Check if pool usage is high before handing out a connection
                self._maybe_expand()

                if self._pool:
                    conn, _ = self._pool.pop()
                    if not conn.health_check():
                        logger.warning("Discarding unhealthy connection")
                        conn.close()
                        self._active -= 1
                        continue
                    return conn

                if self._active < self._max_size:
                    conn = self._factory()
                    self._active += 1
                    return conn

            if time.time() >= deadline:
                logger.error(
                    "Timed out waiting for database connection (active=%d, pool=%d)",
                    self._active,
                    len(self._pool),
                )
                raise TimeoutError("No available connection in pool")

            time.sleep(0.05)

    def release_connection(self, conn: DatabaseConnection) -> None:
        with self._lock:
            self._shrink_idle_connections()
            if not conn.health_check():
                logger.warning("Dropping unhealthy connection on release")
                conn.close()
                self._active -= 1
                return

            if len(self._pool) >= self._max_size:
                logger.warning(
                    "Connection pool full; closing returned connection"
                )
                conn.close()
                self._active -= 1
            else:
                self._pool.append((conn, time.time()))

    def health_check(self) -> bool:
        with self._lock:
            temp: List[Tuple[DatabaseConnection, float]] = []
            healthy = True
            while self._pool:
                conn, ts = self._pool.pop()
                if not conn.health_check():
                    healthy = False
                    logger.warning(
                        "Removing unhealthy idle connection during health check"
                    )
                    conn.close()
                    self._active -= 1
                    if self._max_size > self._initial_size:
                        self._max_size -= 1
                else:
                    temp.append((conn, ts))
            for item in temp:
                self.release_connection(item[0])
            return healthy
