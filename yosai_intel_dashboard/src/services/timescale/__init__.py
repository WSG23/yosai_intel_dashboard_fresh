"""TimescaleDB utilities and models.

This package provides an asynchronous database manager, an optional
adapter with convenience analytics queries, and SQLAlchemy models for
the access event tables.
"""

from .adapter import TimescaleAdapter
from .manager import TimescaleDBManager
from .models import AccessEvent, AccessEvent5Min, Base

__all__ = [
    "TimescaleDBManager",
    "TimescaleAdapter",
    "Base",
    "AccessEvent",
    "AccessEvent5Min",
]
