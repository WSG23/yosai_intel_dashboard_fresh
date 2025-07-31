from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from config import get_cache_config
from core.cache_manager import CacheConfig, InMemoryCacheManager
from error_handling import http_error
from services.cached_analytics import CachedAnalyticsService
from services.security import require_permission
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
    data = _cached_service.get_analytics_summary_sync(query.facility_id, query.range)
    return JSONResponse(content=data)


@router.get("/sources")
async def get_data_sources(_: None = Depends(require_permission("analytics.read"))):
    return JSONResponse(
        content={"sources": [{"value": "test", "label": "Test Data Source"}]}
    )


@router.get("/health")
async def analytics_health(_: None = Depends(require_permission("analytics.read"))):
    return JSONResponse(content={"status": "healthy", "service": "minimal"})


@router.get("/chart/{chart_type}")
async def get_chart_data(
    chart_type: str,
    query: AnalyticsQuery = Depends(),
    _: None = Depends(require_permission("analytics.read")),
):
    data = _cached_service.get_analytics_summary_sync(query.facility_id, query.range)
    if chart_type == "patterns":
        return JSONResponse(content={"type": "patterns", "data": data})
    if chart_type == "timeline":
        return JSONResponse(
            content={"type": "timeline", "data": data.get("hourly_distribution", {})}
        )
    raise http_error(ErrorCode.INVALID_INPUT, "Unknown chart type", 400)
