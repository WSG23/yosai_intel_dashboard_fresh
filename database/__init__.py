"""Database module - compatibility layer for existing app.py"""

# Import from your existing config/database_manager.py
from config.database_manager import DatabaseManager, MockConnection

# Re-export for compatibility
__all__ = ["DatabaseManager", "MockConnection"]
