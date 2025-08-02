from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from yosai_intel_dashboard.src.infrastructure.config import get_cache_config
from yosai_intel_dashboard.src.core.cache_manager import CacheConfig, InMemoryCacheManager
from yosai_intel_dashboard.src.error_handling import http_error
from yosai_intel_dashboard.src.services.cached_analytics import CachedAnalyticsService
from yosai_intel_dashboard.src.services.security import require_permission
from shared.errors.types import ErrorCode

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])

cfg = get_cache_config()
_cache_manager = InMemoryCacheManager(CacheConfig(timeout_seconds=cfg.ttl))
_cached_service = CachedAnalyticsService(_cache_manager)


async def init_cache_manager() -> None:
    await _cache_manager.start()


class AnalyticsQuery(BaseModel):
    facility_id: Optional[str] = Query(default="default")
    range: Optional[str] = Query(default="30d")


@router.get("/patterns")
async def get_patterns_analysis(
    query: AnalyticsQuery = Depends(),
    _: None = Depends(require_permission("analytics.read")),
):
    """Summarize access patterns.

    Fetch aggregated analytics for the requested ``facility_id`` and time ``range``
    and return the cached summary payload.
    """
    data = _cached_service.get_analytics_summary_sync(query.facility_id, query.range)
    return JSONResponse(content=data)


@router.get("/sources")
async def get_data_sources(_: None = Depends(require_permission("analytics.read"))):
    """List available analytics sources.

    Currently returns a static list with test values for demonstration purposes.
    """
    return JSONResponse(
        content={"sources": [{"value": "test", "label": "Test Data Source"}]}
    )


@router.get("/health")
async def analytics_health(_: None = Depends(require_permission("analytics.read"))):
    """Report analytics service health.

    Provides a minimal health payload indicating the analytics component is
    reachable.
    """
    return JSONResponse(content={"status": "healthy", "service": "minimal"})


@router.get("/chart/{chart_type}")
async def get_chart_data(
    chart_type: str,
    query: AnalyticsQuery = Depends(),
    _: None = Depends(require_permission("analytics.read")),
):
    """Retrieve formatted chart data.

    Parameters:
    - **chart_type**: Either ``patterns`` or ``timeline`` specifying the desired
      chart variant.
    - **query**: Common analytics filters including ``facility_id`` and
      reporting ``range``.
    """
    data = _cached_service.get_analytics_summary_sync(query.facility_id, query.range)
    if chart_type == "patterns":
        return JSONResponse(content={"type": "patterns", "data": data})
    if chart_type == "timeline":
        return JSONResponse(
            content={"type": "timeline", "data": data.get("hourly_distribution", {})}
        )
    raise http_error(ErrorCode.INVALID_INPUT, "Unknown chart type", 400)
