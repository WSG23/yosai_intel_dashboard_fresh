"""Database module - compatibility layer for existing app."""

__all__ = ["DatabaseManager", "MockConnection"]


def __getattr__(name: str):
    if name in __all__:
        from yosai_intel_dashboard.src.infrastructure.config.database_manager import DatabaseManager, MockConnection

        return {"DatabaseManager": DatabaseManager, "MockConnection": MockConnection}[
            name
        ]
    raise AttributeError(name)
