from __future__ import annotations

"""Thread-safe connection pool with adaptive sizing and circuit breaking."""

import threading
import time
from typing import Any, Callable, Dict, List, Tuple, Set

from yosai_intel_dashboard.src.infrastructure.config.database_exceptions import (
    ConnectionValidationFailed,
    PoolExhaustedError,
)
from database.types import DatabaseConnection


class CircuitBreaker:
    """Simple circuit breaker implementation."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 30) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failures = 0
        self._opened_at: float | None = None
        self._lock = threading.Lock()

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._opened_at = None

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
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
        shrink_timeout: int,
        *,
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
        self._shrink_timeout = shrink_timeout
        self._threshold = threshold

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
            self._pool.append((conn, time.time()))
            self._active += 1

    # ------------------------------------------------------------------
    def _maybe_expand(self) -> None:
        if self._max_size == 0:
            return
        usage = (self._active - len(self._pool)) / self._max_size
        if usage >= self._threshold and self._max_size < self._max_pool_size:
            self._max_size = min(self._max_size * 2, self._max_pool_size)
            self.metrics["expansions"] += 1

    # ------------------------------------------------------------------
    def _shrink_idle_connections(self) -> None:
        now = time.time()
        new_pool: List[Tuple[DatabaseConnection, float]] = []
        for conn, ts in self._pool:
            if now - ts > self._shrink_timeout and self._max_size > self._min_size:
                conn.close()
                self._active -= 1
                self._max_size -= 1
                self.metrics["shrinks"] += 1
            else:
                new_pool.append((conn, ts))
        self._pool = new_pool

    # ------------------------------------------------------------------
    def get_connection(self) -> DatabaseConnection:
        start = time.time()
        if not self.circuit_breaker.allows_request():
            raise ConnectionValidationFailed("circuit open")
        deadline = start + self._timeout
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
                        continue
                    self.metrics["acquired"] += 1
                    self.metrics["acquire_times"].append(time.time() - start)
                    self.circuit_breaker.record_success()
                    self._in_use.add(conn)
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
                        continue
                    self._active += 1
                    self.metrics["acquired"] += 1
                    self.metrics["acquire_times"].append(time.time() - start)
                    self.circuit_breaker.record_success()
                    self._in_use.add(conn)
                    self._condition.notify()
                    return conn

                remaining = deadline - time.time()
                if remaining <= 0:
                    self.metrics["timeouts"] += 1
                    self.circuit_breaker.record_failure()
                    raise PoolExhaustedError("No available connection in pool")
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
            return healthy

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
