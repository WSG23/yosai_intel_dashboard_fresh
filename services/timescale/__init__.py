"""TimescaleDB utilities and models.

This package provides an asynchronous database manager, an optional
adapter with convenience analytics queries, and SQLAlchemy models for
the access event tables.
"""

from .manager import TimescaleDBManager
from .adapter import TimescaleAdapter
from .models import Base, AccessEvent, AccessEvent5Min

__all__ = [
    "TimescaleDBManager",
    "TimescaleAdapter",
    "Base",
    "AccessEvent",
    "AccessEvent5Min",
]
