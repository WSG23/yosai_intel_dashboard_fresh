from __future__ import annotations

import threading
import time
from typing import Callable, List, Tuple

from database.types import DatabaseConnection


class DatabaseConnectionPool:
    """Connection pool that can grow and shrink based on usage.

    This class is thread-safe: access to the internal state is
    synchronised by a re-entrant lock and a condition variable which
    allows threads to block while waiting for a connection to become
    available.
    """

    def __init__(
        self,
        factory: Callable[[], DatabaseConnection],
        initial_size: int,
        max_size: int,
        timeout: int,
        shrink_timeout: int,
        threshold: float = 0.8,
    ) -> None:
        # Re-entrant lock protects all mutable internal state.  A dedicated
        # condition is used to signal threads waiting for a connection.
        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)
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
        """Increase ``_max_size`` if current usage exceeds the threshold.

        Caller must hold ``_lock`` before invoking this method.
        """
        if self._max_size == 0:
            return
        usage = (self._active - len(self._pool)) / self._max_size
        if usage >= self._threshold and self._max_size < self._max_pool_size:
            self._max_size = min(self._max_size * 2, self._max_pool_size)

    def _shrink_idle_connections(self) -> None:
        """Remove idle connections that have exceeded ``shrink_timeout``.

        Caller must hold ``_lock`` before invoking this method.
        """
        now = time.time()
        new_pool: List[Tuple[DatabaseConnection, float]] = []
        for conn, ts in self._pool:
            if now - ts > self._shrink_timeout and self._max_size > self._initial_size:
                conn.close()
                self._active -= 1
                self._max_size -= 1
            else:
                new_pool.append((conn, ts))
        self._pool = new_pool

    def get_connection(self) -> DatabaseConnection:
        """Acquire a connection from the pool in a thread-safe manner.

        Threads block on the condition variable until a connection is
        available or the ``timeout`` expires.
        """
        deadline = time.time() + self._timeout
        with self._condition:
            while True:
                self._shrink_idle_connections()
                # Check if pool usage is high before handing out a connection
                self._maybe_expand()

                if self._pool:
                    conn, _ = self._pool.pop()
                    if not conn.health_check():
                        conn.close()
                        self._active -= 1
                        continue
                    return conn

                if self._active < self._max_size:
                    conn = self._factory()
                    self._active += 1
                    return conn

                remaining = deadline - time.time()
                if remaining <= 0:
                    raise TimeoutError("No available connection in pool")

                # Wait a short interval to allow other threads to release
                # connections while respecting the overall timeout.
                self._condition.wait(timeout=min(0.05, remaining))

    def release_connection(self, conn: DatabaseConnection) -> None:
        """Return a connection to the pool and notify waiting threads."""
        with self._condition:
            self._shrink_idle_connections()
            if not conn.health_check():
                conn.close()
                self._active -= 1
            elif len(self._pool) >= self._max_size:
                conn.close()
                self._active -= 1
            else:
                self._pool.append((conn, time.time()))
            # Wake one waiting thread (if any) since the pool size or
            # availability may have changed.
            self._condition.notify()

    def health_check(self) -> bool:
        """Check the health of all idle connections."""
        with self._condition:
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
            return healthy
