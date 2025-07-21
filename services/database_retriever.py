from __future__ import annotations

from typing import Any, Dict

from advanced_cache import cache_with_lock

from .db_analytics_helper import DatabaseAnalyticsHelper


class DatabaseAnalyticsRetriever:
    """Wrapper providing cached analytics retrieval from a database."""

    def __init__(self, helper: DatabaseAnalyticsHelper) -> None:
        self.helper = helper

    @cache_with_lock(ttl_seconds=600)
    def get_analytics(self) -> Dict[str, Any]:
        """Return analytics data from the helper."""
        return self.helper.get_analytics()


__all__ = ["DatabaseAnalyticsRetriever"]
