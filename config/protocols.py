from __future__ import annotations

from typing import Any, Callable, Dict, Optional, Protocol, TypeVar

from database.types import DatabaseConnection

T = TypeVar("T")


class RetryConfigProtocol(Protocol):
    max_attempts: int
    base_delay: float
    jitter: bool
    backoff_factor: float
    max_delay: float


class ConnectionRetryManagerProtocol(Protocol):
    def run_with_retry(self, func: Callable[[], T]) -> T: ...


class ConfigLoaderProtocol(Protocol):
    """Load configuration data from a path."""

    def load(self, config_path: Optional[str] = None) -> Any:
        """Return configuration data from ``config_path``."""
        ...


class ConfigValidatorProtocol(Protocol):
    """Validate configuration dictionaries."""

    def validate(self, data: Dict[str, Any]) -> "Config":
        """Validate raw ``data`` and return a :class:`Config` object."""
        ...

    def run_checks(self, config: "Config") -> "ValidationResult":
        """Perform additional validation checks on ``config``."""
        ...


class ConfigTransformerProtocol(Protocol):
    """Transform configuration objects."""

    def transform(self, config: "Config") -> "Config":
        """Apply transformations to ``config`` and return it."""
        ...


class DatabaseManagerProtocol(Protocol):
    """Minimal interface for database manager services."""

    def get_connection(self) -> DatabaseConnection: ...

    def health_check(self) -> bool: ...

    def close(self) -> None: ...


class EnhancedPostgreSQLManagerProtocol(DatabaseManagerProtocol, Protocol):
    """Specialized interface for enhanced PostgreSQL managers."""

    def execute_query_with_retry(
        self, query: str, params: Optional[Dict] | None = None
    ) -> Any: ...

    def health_check_with_retry(self) -> bool: ...


__all__ = [
    "RetryConfigProtocol",
    "ConnectionRetryManagerProtocol",
    "ConfigLoaderProtocol",
    "ConfigValidatorProtocol",
    "ConfigTransformerProtocol",
    "DatabaseManagerProtocol",
    "EnhancedPostgreSQLManagerProtocol",
]
