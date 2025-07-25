"""Asynchronous analytics API exposing WebSocket and SSE feeds."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncIterator, Optional

from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

from core.cache_manager import CacheConfig, InMemoryCacheManager
from core.events import EventBus
from services.cached_analytics import CachedAnalyticsService
from services.common.async_db import get_pool
from services.security import require_permission
from infrastructure.discovery.health_check import (
    setup_health_checks,
    register_health_check,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------

event_bus = EventBus()
cache_manager = InMemoryCacheManager(CacheConfig(timeout_seconds=300))
analytics_service = CachedAnalyticsService(cache_manager)

app = FastAPI(dependencies=[Depends(require_permission("analytics.read"))])


register_health_check(app, "cache", lambda _: True)
register_health_check(app, "event_bus", lambda _: True)
setup_health_checks(app)


async def get_service() -> CachedAnalyticsService:
    """Return the analytics service instance."""
    return analytics_service


@app.on_event("startup")
async def _startup() -> None:
    await cache_manager.start()


# ---------------------------------------------------------------------------
# Middleware to expose connection pool statistics
# ---------------------------------------------------------------------------


class PoolMonitorMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        try:
            pool = await get_pool()
            total = pool.get_size()
            idle = pool.get_idle_size()
            response.headers["X-Pool-Size"] = str(total)
            response.headers["X-Pool-Idle"] = str(idle)
        except Exception:  # pragma: no cover - best effort
            pass
        return response


app.add_middleware(PoolMonitorMiddleware)

# ---------------------------------------------------------------------------
# API endpoints converted from the legacy Flask implementation
# ---------------------------------------------------------------------------


class AnalyticsQuery:
    def __init__(
        self, facility_id: str = Query("default"), range: str = Query("30d")
    ) -> None:
        self.facility_id = facility_id
        self.range = range


@app.get("/api/v1/analytics/patterns")
async def get_patterns_analysis(
    query: AnalyticsQuery = Depends(),
    service: CachedAnalyticsService = Depends(get_service),
):
    data = await service.get_analytics_summary(query.facility_id, query.range)
    return JSONResponse(content=data)


@app.get("/api/v1/analytics/sources")
async def get_data_sources() -> JSONResponse:
    return JSONResponse(
        content={"sources": [{"value": "test", "label": "Test Data Source"}]}
    )


@app.get("/api/v1/analytics/health")
async def analytics_health() -> JSONResponse:
    return JSONResponse(content={"status": "healthy", "service": "minimal"})


@app.get("/api/v1/analytics/chart/{chart_type}")
async def get_chart_data(
    chart_type: str,
    query: AnalyticsQuery = Depends(),
    service: CachedAnalyticsService = Depends(get_service),
):
    data = await service.get_analytics_summary(query.facility_id, query.range)
    if chart_type == "patterns":
        return JSONResponse(content={"type": "patterns", "data": data})
    if chart_type == "timeline":
        return JSONResponse(
            content={"type": "timeline", "data": data.get("hourly_distribution", {})}
        )
    raise HTTPException(status_code=400, detail="Unknown chart type")


@app.get("/api/v1/export/analytics/json")
async def export_analytics_json(
    query: AnalyticsQuery = Depends(),
    service: CachedAnalyticsService = Depends(get_service),
):
    data = await service.get_analytics_summary(query.facility_id, query.range)
    body = json.dumps(data, indent=2)
    headers = {"Content-Disposition": "attachment; filename=analytics_export.json"}
    return StreamingResponse(
        iter([body]), media_type="application/json", headers=headers
    )


@app.get("/api/v1/export/formats")
async def get_export_formats() -> JSONResponse:
    formats = [
        {"type": "csv", "name": "CSV", "description": "Comma-separated values"},
        {"type": "json", "name": "JSON", "description": "JavaScript Object Notation"},
        {"type": "xlsx", "name": "Excel", "description": "Microsoft Excel format"},
    ]
    return JSONResponse(content={"formats": formats})


@app.get("/api/v1/analytics/all")
async def get_all_analytics(
    query: AnalyticsQuery = Depends(),
    service: CachedAnalyticsService = Depends(get_service),
):
    data = await service.get_analytics_summary(query.facility_id, query.range)
    return JSONResponse(content=data)


# ---------------------------------------------------------------------------
# Real-time update feeds
# ---------------------------------------------------------------------------


@app.websocket("/ws/analytics")
async def analytics_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    queue: asyncio.Queue[str] = asyncio.Queue()

    def _handler(payload: dict) -> None:
        queue.put_nowait(json.dumps(payload))

    sid = event_bus.subscribe("analytics_update", _handler)
    try:
        while True:
            msg = await queue.get()
            await websocket.send_text(msg)
    except WebSocketDisconnect:
        pass
    finally:
        event_bus.unsubscribe(sid)


@app.get("/sse/analytics")
async def analytics_sse() -> StreamingResponse:
    queue: asyncio.Queue[str] = asyncio.Queue()

    def _handler(payload: dict) -> None:
        queue.put_nowait(json.dumps(payload))

    sid = event_bus.subscribe("analytics_update", _handler)

    async def _generator() -> AsyncIterator[str]:
        try:
            while True:
                data = await queue.get()
                yield f"data: {data}\n\n"
        finally:
            event_bus.unsubscribe(sid)

    return StreamingResponse(_generator(), media_type="text/event-stream")


__all__ = ["app", "get_service", "event_bus"]
