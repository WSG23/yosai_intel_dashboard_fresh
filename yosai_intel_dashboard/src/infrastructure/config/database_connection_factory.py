"""Factory for creating database connections with retry and pooling support."""

from __future__ import annotations

import logging
from typing import Optional

from yosai_intel_dashboard.src.database.retry_strategy import (  # noqa: F401
    RetryStrategy,
)

from .connection_pool import DatabaseConnectionPool
from .connection_retry import ConnectionRetryManager, RetryConfig
from .database_exceptions import ConnectionRetryExhausted, DatabaseError
from .database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class _RetryLogger:
    """Callback handler that logs retry events."""

    def __init__(self, max_attempts: int) -> None:
        self.max_attempts = max_attempts

    def on_retry(
        self, attempt: int, delay: float
    ) -> None:  # pragma: no cover - simple logging
        logger.warning(
            "Database connection attempt %d/%d failed; retrying in %.2fs",
            attempt,
            self.max_attempts,
            delay,
        )

    def on_success(self) -> None:  # pragma: no cover - simple logging
        logger.info("Database connection established")

    def on_failure(self) -> None:  # pragma: no cover - simple logging
        logger.error("Database connection failed after %d attempts", self.max_attempts)


class DatabaseConnectionFactory:
    """Create database connections with retry and optional pooling."""

    def __init__(
        self,
        manager: DatabaseManager,
        retry_config: Optional[RetryConfig] = None,
    ) -> None:
        self._manager = manager
        self._retry_config = retry_config or RetryConfig()
        self._retry = ConnectionRetryManager(
            self._retry_config, callbacks=_RetryLogger(self._retry_config.max_attempts)
        )

    def _create_connection_with_retry(self):
        # Local import to avoid circular dependency
        from yosai_intel_dashboard.src.utils.text_utils import safe_text

        try:
            return self._retry.run_with_retry(
                self._manager._create_connection  # type: ignore[attr-defined]
            )
        except ConnectionRetryExhausted as exc:  # pragma: no cover - defensive
            logger.error(
                "Exhausted retries creating database connection: %s", safe_text(exc)
            )
            raise
        except DatabaseError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(
                "Unexpected error creating database connection: %s", safe_text(exc)
            )
            raise DatabaseError(safe_text(exc)) from exc

    def create_pool(
        self,
        initial_size: int,
        max_size: int,
        timeout: int,
        shrink_timeout: int,
    ) -> DatabaseConnectionPool:
        """Create a connection pool using the retrying connection factory."""

        pool = DatabaseConnectionPool(
            self._create_connection_with_retry,
            initial_size,
            max_size,
            timeout,
            shrink_timeout,
        )
        logger.info(
            "Created connection pool initial_size=%d max_size=%d",
            initial_size,
            max_size,
        )
        return pool

    def create_connection(self):
        """Create a single database connection using retry strategy."""

        return self._create_connection_with_retry()


__all__ = ["DatabaseConnectionFactory", "RetryStrategy"]
