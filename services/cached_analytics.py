from __future__ import annotations

"""Analytics service with caching using :class:`CacheManager`."""

from typing import Any, Dict

from core.cache_manager import CacheManager
from services.analytics_summary import generate_sample_analytics


class CachedAnalyticsService:
    """Provide cached analytics summaries."""

    def __init__(self, cache_manager: CacheManager, ttl_seconds: int = 300) -> None:
        self.cache_manager = cache_manager
        self.ttl_seconds = ttl_seconds

    async def _compute_metrics(self, facility_id: str, date_range: str) -> Dict[str, Any]:
        """Compute analytics metrics for the given parameters."""
        result = generate_sample_analytics()
        result["facility_id"] = facility_id
        result["requested_range"] = date_range
        return result

    async def get_analytics_summary(self, facility_id: str, date_range: str) -> Dict[str, Any]:
        """Return cached analytics summary or compute and store it."""
        key = f"analytics:{facility_id}:{date_range}"
        cached = await self.cache_manager.get(key)
        if cached is not None:
            return cached
        metrics = await self._compute_metrics(facility_id, date_range)
        await self.cache_manager.set(key, metrics, self.ttl_seconds)
        return metrics


__all__ = ["CachedAnalyticsService"]
