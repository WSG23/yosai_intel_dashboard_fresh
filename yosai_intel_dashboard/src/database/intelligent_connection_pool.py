from __future__ import annotations

"""Thread-safe connection pool with adaptive sizing and circuit breaking."""

import asyncio
import threading
import time
from contextlib import asynccontextmanager, contextmanager
from typing import Any, Callable, Dict, List, Tuple

from yosai_intel_dashboard.src.database.types import DatabaseConnection
from yosai_intel_dashboard.src.infrastructure.config.database_exceptions import (
    ConnectionValidationFailed,
)
from yosai_intel_dashboard.src.infrastructure.monitoring.error_budget import (
    record_error,
)
from yosai_intel_dashboard.src.infrastructure.monitoring.prometheus.connection_pool import (
    db_pool_active_connections,
    db_pool_current_size,
    db_pool_wait_seconds,
)


class CircuitBreaker:
    """Simple circuit breaker implementation."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        name: str = "connection_pool",
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failures = 0
        self._opened_at: float | None = None
        self._lock = threading.Lock()
        self._name = name

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._opened_at = None

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            record_error(self._name)
            if self._failures >= self.failure_threshold:
                self._opened_at = time.time()

    def allows_request(self) -> bool:
        with self._lock:
            if self._opened_at is None:
                return True
            if time.time() - self._opened_at >= self.recovery_timeout:
                self._failures = 0
                self._opened_at = None
                return True
            return False


class IntelligentConnectionPool:
    """Connection pool with dynamic scaling, metrics, and circuit breaking."""

    def __init__(
        self,
        factory: Callable[[], DatabaseConnection],
        min_size: int,
        max_size: int,
        timeout: int,
        shrink_timeout: int | None = None,
        *,
        shrink_interval: float = 0,
        idle_timeout: int | None = None,
        failure_threshold: int = 5,
        recovery_timeout: int = 30,
        threshold: float = 0.75,
    ) -> None:
        self._lock = threading.RLock()
        self._condition = threading.Condition(self._lock)
        self._factory = factory
        self._min_size = min_size
        self._max_pool_size = max(max_size, min_size)
        self._max_size = min_size
        self._timeout = timeout
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
        self.circuit_breaker = CircuitBreaker(failure_threshold, recovery_timeout)
        self.metrics: Dict[str, Any] = {
            "acquired": 0,
            "released": 0,
            "failed": 0,
            "timeouts": 0,
            "expansions": 0,
            "shrinks": 0,
            "acquire_times": [],
        }

        for _ in range(min_size):
            conn = self._factory()
            self._warm_connection(conn)
            self._pool.append((conn, time.time()))
            self._active += 1

        self._update_metrics()

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
        db_pool_current_size.set(self._max_size)
        db_pool_active_connections.set(self._active - len(self._pool))

    # ------------------------------------------------------------------
    def _maybe_expand(self) -> None:
        if self._max_size == 0:
            return
        usage = (self._active - len(self._pool)) / self._max_size
        if usage >= self._threshold and self._max_size < self._max_pool_size:
            self._max_size = min(self._max_size * 2, self._max_pool_size)
            self.metrics["expansions"] += 1
            self._update_metrics()

    # ------------------------------------------------------------------
    def _shrink_idle_connections(self) -> None:
        now = time.time()
        new_pool: List[Tuple[DatabaseConnection, float]] = []
        for conn, ts in self._pool:
            if now - ts > self._idle_timeout and self._max_size > self._min_size:
                conn.close()
                self._active -= 1
                self._max_size -= 1
                self.metrics["shrinks"] += 1
            else:
                new_pool.append((conn, ts))
        self._pool = new_pool
        self._update_metrics()

    # ------------------------------------------------------------------
    def _periodic_shrink(self) -> None:
        while not self._shutdown:
            time.sleep(self._shrink_interval)
            with self._condition:
                self._shrink_idle_connections()

    def close(self) -> None:
        self._shutdown = True
        if self._shrink_thread is not None:
            self._shrink_thread.join(timeout=0.1)

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
                    self.metrics["failed"] += 1
            self._pool = new_pool

            while self._active < self._min_size:
                conn = self._factory()
                self._warm_connection(conn)
                self._pool.append((conn, time.time()))
                self._active += 1

            self._update_metrics()

    # ------------------------------------------------------------------
    def get_connection(self, *, timeout: float | None = None) -> DatabaseConnection:
        start = time.time()
        if not self.circuit_breaker.allows_request():
            raise ConnectionValidationFailed("circuit open")
        deadline = start + (timeout if timeout is not None else self._timeout)
        with self._condition:
            while True:
                self._shrink_idle_connections()
                self._maybe_expand()

                if self._pool:
                    conn, _ = self._pool.pop()
                    if not conn.health_check():
                        conn.close()
                        self._active -= 1
                        self.metrics["failed"] += 1
                        self.circuit_breaker.record_failure()
                        if not self.circuit_breaker.allows_request():
                            raise ConnectionValidationFailed("circuit open")
                        self._update_metrics()
                        continue
                    self.metrics["acquired"] += 1
                    wait = time.time() - start
                    self.metrics["acquire_times"].append(wait)
                    self.circuit_breaker.record_success()
                    self._in_use.add(conn)
                    self._update_metrics()
                    db_pool_wait_seconds.observe(wait)

                    self._condition.notify()
                    return conn

                if self._active < self._max_size:
                    conn = self._factory()
                    if not conn.health_check():
                        conn.close()
                        self.metrics["failed"] += 1
                        self.circuit_breaker.record_failure()
                        if not self.circuit_breaker.allows_request():
                            raise ConnectionValidationFailed("circuit open")
                        self._update_metrics()
                        continue
                    self._active += 1
                    self.metrics["acquired"] += 1
                    wait = time.time() - start
                    self.metrics["acquire_times"].append(wait)
                    self.circuit_breaker.record_success()
                    self._in_use.add(conn)
                    self._update_metrics()
                    db_pool_wait_seconds.observe(wait)
                    self._condition.notify()
                    return conn

                remaining = deadline - time.time()
                if remaining <= 0:
                    self.metrics["timeouts"] += 1
                    self.circuit_breaker.record_failure()
                    db_pool_wait_seconds.observe(time.time() - start)
                    raise TimeoutError("No available connection in pool")

                self._condition.wait(timeout=remaining)

    # ------------------------------------------------------------------
    def release_connection(self, conn: DatabaseConnection) -> None:
        with self._condition:
            self._shrink_idle_connections()
            self._in_use.discard(conn)
            if not conn.health_check():
                conn.close()
                self._active -= 1
                self.metrics["failed"] += 1
                self.circuit_breaker.record_failure()
                self._update_metrics()
                return

            if self._max_size == 0:
                conn.close()
                self._condition.notify()
                return

            if len(self._pool) >= self._max_size:
                conn.close()
                self._active -= 1
            else:
                self._pool.append((conn, time.time()))
            self.metrics["released"] += 1
            self._update_metrics()
            self._condition.notify()

    # ------------------------------------------------------------------
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
                    self.metrics["failed"] += 1
                    if self._max_size > self._min_size:
                        self._max_size -= 1
                else:
                    temp.append((conn, ts))
            for item in temp:
                self.release_connection(item[0])
            if not healthy:
                self.circuit_breaker.record_failure()
            else:
                self.circuit_breaker.record_success()
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

    # ------------------------------------------------------------------
    def get_metrics(self) -> Dict[str, Any]:
        data = self.metrics.copy()
        times = data.pop("acquire_times")
        data["avg_acquire_time"] = (sum(times) / len(times)) if times else 0.0
        data["active"] = self._active
        data["max_size"] = self._max_size
        return data

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
            self._condition.notify_all()


__all__ = ["IntelligentConnectionPool", "CircuitBreaker"]
