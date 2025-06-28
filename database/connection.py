"""Database connection - compatible with existing codebase"""

import pandas as pd
from typing import Optional, Protocol
from config.database_manager import DatabaseManager, MockConnection


class DatabaseConnection(Protocol):
    """Database connection protocol"""

    def execute_query(self, query: str, params: Optional[tuple] = None) -> pd.DataFrame:
        """Execute SELECT query and return DataFrame"""
        ...

    def execute_command(self, command: str, params: Optional[tuple] = None) -> int:
        """Execute INSERT/UPDATE/DELETE and return affected rows"""
        ...

    def health_check(self) -> bool:
        """Check if database is accessible"""
        ...


def create_database_connection() -> DatabaseConnection:
    """Create database connection using existing DatabaseManager"""
    # Use your existing database manager
    from config.config import get_config

    config_manager = get_config()
    db_config = config_manager.get_database_config()

    # Create database manager with existing config
    db_manager = DatabaseManager(
        db_type=db_config.type,
        connection_string=getattr(db_config, 'connection_string', ''),
        **db_config.__dict__
    )

    return db_manager.get_connection()


# For compatibility with existing imports
__all__ = ['DatabaseConnection', 'create_database_connection', 'DatabaseManager', 'MockConnection']
