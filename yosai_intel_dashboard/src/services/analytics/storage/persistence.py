from __future__ import annotations

"""Persistence initialization helpers."""

from typing import Any, Callable, Tuple

from yosai_intel_dashboard.src.infrastructure.config.database_manager import DatabaseSettings

from yosai_intel_dashboard.src.services.helpers.database_initializer import initialize_database


class PersistenceManager:
    """Initialize database connections for analytics."""

    def initialize(
        self,
        database: Any | None,
        *,
        settings: DatabaseSettings | None = None,
        settings_provider: Callable[[], DatabaseSettings] | None = None,
    ) -> Tuple[Any | None, Any, Any]:
        return initialize_database(
            database,
            settings=settings,
            settings_provider=settings_provider,
        )


__all__ = ["PersistenceManager"]
