from __future__ import annotations

from typing import Any, Dict

from yosai_intel_dashboard.src.core.cache_manager import CacheConfig, InMemoryCacheManager, cache_with_lock

_cache_manager = InMemoryCacheManager(CacheConfig())

from .db_analytics_helper import DatabaseAnalyticsHelper
from yosai_intel_dashboard.src.core.interfaces.service_protocols import DatabaseAnalyticsRetrieverProtocol


class DatabaseAnalyticsRetriever(DatabaseAnalyticsRetrieverProtocol):
    """Wrapper providing cached analytics retrieval from a database."""

    def __init__(self, helper: DatabaseAnalyticsHelper) -> None:
        self.helper = helper

    @cache_with_lock(_cache_manager, ttl=600)
    def get_analytics(self) -> Dict[str, Any]:
        """Return analytics data from the helper."""
        return self.helper.get_analytics()


__all__ = ["DatabaseAnalyticsRetriever"]
