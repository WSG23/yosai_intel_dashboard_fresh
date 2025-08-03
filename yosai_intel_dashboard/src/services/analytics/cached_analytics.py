from __future__ import annotations

"""Analytics service with caching using :class:`CacheManager`."""

import asyncio
from typing import Any, Dict

from src.common.events import EventBus
from yosai_intel_dashboard.src.core.cache_manager import CacheManager
from yosai_intel_dashboard.src.services.analytics_summary import generate_sample_analytics


class CachedAnalyticsService:
    """Provide cached analytics summaries."""

    def __init__(
        self,
        cache_manager: CacheManager,
        ttl_seconds: int = 300,
        event_bus: EventBus | None = None,
    ) -> None:
        self.cache_manager = cache_manager
        self.ttl_seconds = ttl_seconds
        self.event_bus = event_bus

    async def _compute_metrics(
        self, facility_id: str, date_range: str
    ) -> Dict[str, Any]:
        """Compute analytics metrics for the given parameters."""
        result = generate_sample_analytics()
        result["facility_id"] = facility_id
        result["requested_range"] = date_range
        return result

    async def get_analytics_summary(
        self, facility_id: str, date_range: str
    ) -> Dict[str, Any]:
        """Return cached analytics summary or compute and store it."""
        key = f"analytics:{facility_id}:{date_range}"
        cached = await self.cache_manager.get(key)
        if cached is not None:
            return cached
        metrics = await self._compute_metrics(facility_id, date_range)
        await self.cache_manager.set(key, metrics, self.ttl_seconds)
        if self.event_bus:
            try:
                self.event_bus.emit("analytics_update", metrics)
            except Exception:  # pragma: no cover - best effort
                pass
        return metrics

    def get_analytics_summary_sync(
        self, facility_id: str, date_range: str
    ) -> Dict[str, Any]:
        """Synchronous wrapper for :meth:`get_analytics_summary`."""
        return asyncio.run(self.get_analytics_summary(facility_id, date_range))


__all__ = ["CachedAnalyticsService"]
