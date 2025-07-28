from __future__ import annotations

"""Adaptive connection pool that adjusts size based on usage.

The :class:`IntelligentConnectionPool` automatically expands or shrinks
its pool of connections depending on current demand. Use ``acquire`` and
``release`` like a standard connection pool to obtain connections while
metrics are tracked for analysis.
"""

import threading
import time
from typing import Callable, Dict, List, Tuple, Any

from database.types import DatabaseConnection


class IntelligentConnectionPool:
    """Connection pool with dynamic scaling and simple metrics."""

    def __init__(
        self,
        factory: Callable[[], DatabaseConnection],
        min_size: int,
        max_size: int,
        timeout: int,
        shrink_timeout: int,
        *,
        threshold: float = 0.75,
    ) -> None:
        self._factory = factory
        self._min_size = min_size
        self._max_pool_size = max(max_size, min_size)
        self._max_size = min_size
        self._timeout = timeout
        self._shrink_timeout = shrink_timeout
        self._threshold = threshold

        self._pool: List[Tuple[DatabaseConnection, float]] = []
        self._active = 0
        self._lock = threading.RLock()
        self._metrics: Dict[str, Any] = {
            "acquired": 0,
            "released": 0,
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
        usage = (self._active - len(self._pool)) / max(self._max_size, 1)
        if usage >= self._threshold and self._max_size < self._max_pool_size:
            self._max_size = min(self._max_size * 2, self._max_pool_size)
            self._metrics["expansions"] += 1

    # ------------------------------------------------------------------
    def _shrink_idle_connections(self) -> None:
        now = time.time()
        new_pool: List[Tuple[DatabaseConnection, float]] = []
        for conn, ts in self._pool:
            if (
                now - ts > self._shrink_timeout
                and self._max_size > self._min_size
            ):
                conn.close()
                self._active -= 1
                self._max_size -= 1
                self._metrics["shrinks"] += 1
            else:
                new_pool.append((conn, ts))
        self._pool = new_pool

    # ------------------------------------------------------------------
    def get_connection(self) -> DatabaseConnection:
        start = time.time()
        deadline = start + self._timeout
        while True:
            with self._lock:
                self._shrink_idle_connections()
                self._maybe_expand()

                if self._pool:
                    conn, _ = self._pool.pop()
                    if not conn.health_check():
                        conn.close()
                        self._active -= 1
                        continue
                    self._metrics["acquired"] += 1
                    self._metrics["acquire_times"].append(time.time() - start)
                    return conn

                if self._active < self._max_size:
                    conn = self._factory()
                    self._active += 1
                    self._metrics["acquired"] += 1
                    self._metrics["acquire_times"].append(time.time() - start)
                    return conn

            if time.time() >= deadline:
                raise TimeoutError("No available connection in pool")
            time.sleep(0.05)

    # ------------------------------------------------------------------
    def release_connection(self, conn: DatabaseConnection) -> None:
        with self._lock:
            self._shrink_idle_connections()
            if not conn.health_check():
                conn.close()
                self._active -= 1
                return

            if len(self._pool) >= self._max_size:
                conn.close()
                self._active -= 1
            else:
                self._pool.append((conn, time.time()))
            self._metrics["released"] += 1

    # ------------------------------------------------------------------
    def get_metrics(self) -> Dict[str, Any]:
        data = self._metrics.copy()
        times = data.pop("acquire_times")
        data["avg_acquire_time"] = (sum(times) / len(times)) if times else 0.0
        data["active"] = self._active
        data["max_size"] = self._max_size
        return data


__all__ = ["IntelligentConnectionPool"]
