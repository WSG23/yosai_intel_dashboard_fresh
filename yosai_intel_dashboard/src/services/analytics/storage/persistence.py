from __future__ import annotations

"""Persistence initialization helpers."""

from typing import Any, Tuple

from yosai_intel_dashboard.src.services.helpers.database_initializer import initialize_database


class PersistenceManager:
    """Initialize database connections for analytics."""

    def initialize(self, database: Any | None) -> Tuple[Any | None, Any, Any]:
        return initialize_database(database)


__all__ = ["PersistenceManager"]
