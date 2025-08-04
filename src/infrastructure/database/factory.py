"""Database manager factory helpers.

This module provides convenience functions to construct
:class:`DatabaseManager` instances either from a pre-built
:class:`DatabaseConfig` object or from the current process environment.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class DatabaseConfig:
    """Simple database configuration container."""

    host: str = "localhost"
    port: int = 5432
    name: str = "app.db"
    user: str = "user"
    password: str = ""
    initial_pool_size: int = 1
    max_pool_size: int = 5
    type: str = "sqlite"


class DatabaseManager:
    """Very small stand-in database manager.

    The manager does not establish real connections; it merely stores the
    provided :class:`DatabaseConfig` for use by higher layers or tests.
    """

    def __init__(self, config: DatabaseConfig) -> None:
        self.config = config


def _normalize_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Return a copy of *data* with numeric fields coerced to ``int``.

    This performs minimal validation ensuring values expected to be integers can
    be converted. A :class:`ValueError` is raised when conversion fails.
    """

    result = dict(data)
    for key in ("port", "initial_pool_size", "max_pool_size"):
        if key in result and isinstance(result[key], str):
            try:
                result[key] = int(result[key])
            except ValueError as exc:  # pragma: no cover - defensive
                raise ValueError(f"{key} must be an integer") from exc
    return result


def create_manager(config: DatabaseConfig | Dict[str, Any]) -> DatabaseManager:
    """Create a :class:`DatabaseManager` from configuration.

    Parameters
    ----------
    config:
        Either a :class:`DatabaseConfig` instance or a dictionary with the
        corresponding fields.
    """

    if isinstance(config, dict):
        config = DatabaseConfig(**_normalize_dict(config))
    elif not isinstance(config, DatabaseConfig):
        raise TypeError("config must be DatabaseConfig or dict")
    return DatabaseManager(config)


def create_from_env() -> DatabaseManager:
    """Construct a :class:`DatabaseManager` from environment variables.

    The following variables are consulted with sensible defaults when absent:
    ``DB_HOST``, ``DB_PORT``, ``DB_NAME``, ``DB_USER``, ``DB_PASSWORD``,
    ``DB_MIN_CONN`` and ``DB_MAX_CONN``.
    """

    data: Dict[str, Any] = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": os.getenv("DB_PORT", "5432"),
        "name": os.getenv("DB_NAME", "app.db"),
        "user": os.getenv("DB_USER", "user"),
        "password": os.getenv("DB_PASSWORD", ""),
        "initial_pool_size": os.getenv("DB_MIN_CONN", "1"),
        "max_pool_size": os.getenv("DB_MAX_CONN", "5"),
    }

    data = _normalize_dict(data)
    min_conn = data["initial_pool_size"]
    max_conn = data["max_pool_size"]
    if min_conn < 0 or max_conn < 1 or min_conn > max_conn:
        raise ValueError("invalid connection pool configuration")

    return create_manager(data)


__all__ = [
    "DatabaseConfig",
    "DatabaseManager",
    "create_manager",
    "create_from_env",
]
