from __future__ import annotations

"""Connection wrapper that applies :class:`RetryStrategy` to operations.

The class is internal (note the leading underscore) and is primarily used in
tests.  It acquires a connection from a pool for each attempt and releases it
back to the pool when finished.  Calls can supply override ``attempts`` and
``backoff`` values which are forwarded to :class:`RetryStrategy.run`.
"""

from typing import Any, Callable, TypeVar

from .retry_strategy import RetryStrategy

T = TypeVar("T")


class _PooledConnection:
    def __init__(self, pool: Any, retry: RetryStrategy | None = None) -> None:
        self._pool = pool
        self._retry = retry or RetryStrategy()

    def call(
        self,
        op: Callable[[Any], T],
        *,
        attempts: int | None = None,
        backoff: float | None = None,
    ) -> T:
        """Execute ``op`` with a connection from the pool.

        ``op`` is a callable that receives a single connection argument.  The
        retry behaviour can be tuned per-call using ``attempts`` and
        ``backoff``.
        """

        def use_conn() -> T:
            conn = self._pool.get_connection()
            try:
                return op(conn)
            finally:
                self._pool.release_connection(conn)

        return self._retry.run(use_conn, attempts=attempts, backoff=backoff)


__all__ = ["_PooledConnection"]
