from __future__ import annotations

"""Factory for creating database connections with pluggable retry support."""

from typing import TYPE_CHECKING, Callable, Protocol, TypeVar

from database.types import DatabaseConnection

from .connection_retry import ConnectionRetryManager

if TYPE_CHECKING:  # pragma: no cover
    from .schema import DatabaseSettings  # noqa: F401

T = TypeVar("T")


class RetryStrategy(Protocol):
    """Protocol for retry strategies used by the factory."""

    def run_with_retry(self, func: Callable[[], T]) -> T: ...


class DatabaseConnectionFactory:
    """Create database connections using an optional :class:`RetryStrategy`."""

    def __init__(
        self,
        config: "DatabaseSettings",
        *,
        retry_strategy: RetryStrategy | None = None,
    ) -> None:
        from .database_manager import DatabaseManager

        self._config = config
        self._retry_strategy = retry_strategy or ConnectionRetryManager()
        self._manager = DatabaseManager(config)

    def create(self) -> DatabaseConnection:
        """Create a connection using the configured retry strategy."""

        def _connect() -> DatabaseConnection:
            return self._manager.get_connection()

        return self._retry_strategy.run_with_retry(_connect)
