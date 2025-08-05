from __future__ import annotations

import asyncio
import logging
import threading
import time
from contextlib import asynccontextmanager, contextmanager
from typing import Callable, List, Tuple

from yosai_intel_dashboard.src.database.types import DatabaseConnection

from .database_exceptions import ConnectionValidationFailed, PoolExhaustedError

logger = logging.getLogger(__name__)

from ..monitoring.prometheus.connection_pool import (
    db_pool_active_connections,
    db_pool_current_size,
    db_pool_wait_seconds,
)


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
        shrink_timeout: int | None = None,
        *,
        shrink_interval: float = 0,
        idle_timeout: int | None = None,
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
        self._shrink_timeout = shrink_timeout if shrink_timeout is not None else 0
        if idle_timeout is None:
            idle_timeout = shrink_timeout if shrink_timeout is not None else 0
        self._idle_timeout = idle_timeout
        self._threshold = threshold
        self._shrink_interval = shrink_interval
        self._shutdown = False
        self._shrink_thread: threading.Thread | None = None

        self._pool: List[Tuple[DatabaseConnection, float]] = []
        self._active = 0
        self._in_use: Set[DatabaseConnection] = set()

        for _ in range(initial_size):
            conn = self._factory()
            self._warm_connection(conn)
            self._pool.append((conn, time.time()))
            self._active += 1

        self._update_metrics()

        if self._shrink_interval > 0:
            self._shrink_thread = threading.Thread(
                target=self._periodic_shrink, daemon=True
            )
            self._shrink_thread.start()

    # ------------------------------------------------------------------
    def _warm_connection(self, conn: DatabaseConnection) -> None:
        """Run a lightweight query to validate and warm a connection."""
        try:
            if hasattr(conn, "execute_query"):
                conn.execute_query("SELECT 1")
            elif not conn.health_check():
                raise ConnectionValidationFailed("initial connection validation failed")
        except Exception as exc:  # pragma: no cover - defensive
            raise ConnectionValidationFailed(
                "initial connection validation failed"
            ) from exc

    def _update_metrics(self) -> None:
        """Update Prometheus gauges to reflect pool state."""
        db_pool_current_size.set(self._max_size)
        db_pool_active_connections.set(self._active - len(self._pool))

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
            if now - ts > self._idle_timeout and self._max_size > self._initial_size:
                conn.close()
                self._active -= 1
                self._max_size -= 1
            else:
                new_pool.append((conn, ts))
        self._pool = new_pool

    def _periodic_shrink(self) -> None:
        while not self._shutdown:
            time.sleep(self._shrink_interval)
            with self._condition:
                self._shrink_idle_connections()

    def get_connection(self, *, timeout: float | None = None) -> DatabaseConnection:
        """Acquire a connection from the pool in a thread-safe manner.

        Threads block on the condition variable until a connection is
        available or the ``timeout`` expires.
        """
        start = time.time()
        deadline = start + (timeout if timeout is not None else self._timeout)
        with self._condition:
            while True:

                self._shrink_idle_connections()
                # Check if pool usage is high before handing out a connection
                self._maybe_expand()

                if self._pool:
                    conn, _ = self._pool.pop()
                    if not conn.health_check():
                        logger.warning("Discarding unhealthy connection")
                        conn.close()
                        self._active -= 1
                        self._update_metrics()
                        continue
                    self._in_use.add(conn)
                    self._update_metrics()
                    db_pool_wait_seconds.observe(time.time() - start)

                    return conn

                if self._active < self._max_size:
                    conn = self._factory()
                    self._warm_connection(conn)
                    self._active += 1
                    self._in_use.add(conn)
                    self._update_metrics()
                    db_pool_wait_seconds.observe(time.time() - start)
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
            self._in_use.discard(conn)
            if not conn.health_check():
                logger.warning("Dropping unhealthy connection on release")
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

    # ------------------------------------------------------------------
    def close_all(self) -> None:
        """Close all connections and prevent further use."""
        with self._condition:
            for conn, _ in self._pool:
                conn.close()
            self._pool.clear()
            for conn in list(self._in_use):
                conn.close()
            self._in_use.clear()
            self._active = 0
            self._max_size = 0
            self._shutdown = True
            if self._shrink_thread is not None:
                self._shrink_thread.join(timeout=0.1)
            self._condition.notify_all()

    # ------------------------------------------------------------------
    def warmup(self) -> None:
        """Ensure the pool is filled and connections are warmed."""
        with self._condition:
            new_pool: List[Tuple[DatabaseConnection, float]] = []
            for conn, _ in self._pool:
                try:
                    self._warm_connection(conn)
                    new_pool.append((conn, time.time()))
                except ConnectionValidationFailed:
                    conn.close()
                    self._active -= 1
            self._pool = new_pool

            while self._active < self._initial_size:
                conn = self._factory()
                self._warm_connection(conn)
                self._pool.append((conn, time.time()))
                self._active += 1

            self._update_metrics()

    def health_check(self) -> bool:
        """Check the health of all idle connections."""
        with self._condition:
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
            self._update_metrics()
            return healthy

    @contextmanager
    def acquire(self, *, timeout: float | None = None):
        """Context manager to acquire a connection with optional timeout."""
        conn = self.get_connection(timeout=timeout)
        try:
            yield conn
        finally:
            self.release_connection(conn)

    @asynccontextmanager
    async def acquire_async(self, *, timeout: float | None = None):
        """Async context manager for acquiring a connection without blocking the loop."""
        conn = await asyncio.to_thread(self.get_connection, timeout=timeout)
        try:
            yield conn
        finally:
            await asyncio.to_thread(self.release_connection, conn)
