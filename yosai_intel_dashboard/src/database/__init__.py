"""Database module - compatibility layer for existing app."""

from .mock_database import MockDatabase
from .protocols import ConnectionProtocol
from .shard_resolver import ShardResolver

__all__ = [
    "DatabaseManager",
    "MockConnection",
    "MockDatabase",
    "ConnectionProtocol",
    "ShardResolver",
]


def __getattr__(name: str):

    if name in {"DatabaseManager", "MockConnection"}:
        from yosai_intel_dashboard.src.infrastructure.config.database_manager import (
            DatabaseManager,
            MockConnection,
        )

        return {"DatabaseManager": DatabaseManager, "MockConnection": MockConnection}[
            name
        ]
    if name == "MockDatabase":
        return MockDatabase
    if name == "ConnectionProtocol":
        return ConnectionProtocol

    raise AttributeError(name)
