"""Database module - compatibility layer for existing app."""

from __future__ import annotations

import warnings

__all__ = ["DatabaseConnectionFactory", "DatabaseManager", "MockConnection"]


def __getattr__(name: str):
    if name == "DatabaseConnectionFactory":
        from yosai_intel_dashboard.src.infrastructure.config.database_manager import (
            DatabaseConnectionFactory,
        )

        return DatabaseConnectionFactory

    if name in {"DatabaseManager", "MockConnection"}:
        from yosai_intel_dashboard.src.infrastructure.config.database_manager import (
            DatabaseManager,
            MockConnection,
        )

        warnings.warn(
            f"{name} is deprecated; use DatabaseConnectionFactory instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return {"DatabaseManager": DatabaseManager, "MockConnection": MockConnection}[name]
    raise AttributeError(name)
