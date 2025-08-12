from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

from shared.errors.types import ErrorCode
from yosai_intel_dashboard.src.adapters.api.cache import cached_json_response
from yosai_intel_dashboard.src.core.cache_manager import (
    CacheConfig,
    InMemoryCacheManager,
)
from yosai_intel_dashboard.src.core.security import validate_user_input
from yosai_intel_dashboard.src.error_handling import http_error
from yosai_intel_dashboard.src.infrastructure.config import get_cache_config
from yosai_intel_dashboard.src.services.analytics.proficiency_endpoint import (
    router as proficiency_router,
)
from yosai_intel_dashboard.src.components.analytics.real_time_dashboard import (
    router as realtime_router,
)
from yosai_intel_dashboard.src.services.cached_analytics import CachedAnalyticsService
from yosai_intel_dashboard.src.services.security import require_permission
from yosai_intel_dashboard.src.core import registry

# Routes now use an unversioned prefix and are mounted under /v1 by the
# adapter. This simplifies preparing future versions while keeping unversioned
# paths available for backward compatibility.
router = APIRouter(prefix="/analytics", tags=["analytics"])

cfg = get_cache_config()
_cache_manager = InMemoryCacheManager(CacheConfig(timeout_seconds=cfg.ttl))
registry.register(
    "cached_analytics_service", CachedAnalyticsService(_cache_manager)
)
router.include_router(proficiency_router)
router.include_router(realtime_router)


async def init_cache_manager() -> None:
    await _cache_manager.start()


class AnalyticsQuery(BaseModel):
    facility_id: Optional[str] = Query(default="default")
    range: Optional[str] = Query(default="30d")

    model_config = ConfigDict(
        json_schema_extra={"examples": [{"facility_id": "fac-123", "range": "7d"}]}
    )


@router.get("/patterns")
async def get_patterns_analysis(
    query: AnalyticsQuery = Depends(),
    _: None = Depends(require_permission("analytics.read")),
):
    """Summarize access patterns.

    Fetch aggregated analytics for the requested ``facility_id`` and time ``range``
    and return the cached summary payload.
    """
    facility_id = validate_user_input(query.facility_id or "", "facility_id")
    range_val = validate_user_input(query.range or "", "range")
    service = registry.get("cached_analytics_service")
    data = service.get_analytics_summary_sync(facility_id, range_val)
    return cached_json_response(data, max_age=cfg.ttl)


@router.get("/sources")
async def get_data_sources(_: None = Depends(require_permission("analytics.read"))):
    """List available analytics sources.

    Currently returns a static list with test values for demonstration purposes.
    """
    return cached_json_response(
        {"sources": [{"value": "test", "label": "Test Data Source"}]},
        max_age=cfg.ttl,
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
    chart_type = validate_user_input(chart_type, "chart_type")
    facility_id = validate_user_input(query.facility_id or "", "facility_id")
    range_val = validate_user_input(query.range or "", "range")
    service = registry.get("cached_analytics_service")
    data = service.get_analytics_summary_sync(facility_id, range_val)
    if chart_type == "patterns":
        return cached_json_response({"type": "patterns", "data": data}, max_age=cfg.ttl)
    if chart_type == "timeline":
        return cached_json_response(
            {"type": "timeline", "data": data.get("hourly_distribution", {})},
            max_age=cfg.ttl,
        )
    raise http_error(ErrorCode.INVALID_INPUT, "Unknown chart type", 400)
