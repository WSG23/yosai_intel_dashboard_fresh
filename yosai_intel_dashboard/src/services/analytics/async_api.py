"""Asynchronous analytics API exposing WebSocket and SSE feeds."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Dict

from fastapi import (
    Depends,
    FastAPI,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.types import ASGIApp

from yosai_intel_dashboard.src.core.cache_manager import (
    CacheConfig,
    InMemoryCacheManager,
)
from yosai_intel_dashboard.src.error_handling import http_error
from yosai_intel_dashboard.src.services.analytics.analytics_service import (
    get_analytics_service,
)
from yosai_intel_dashboard.src.services.cached_analytics import CachedAnalyticsService
from yosai_intel_dashboard.src.core import registry
from yosai_intel_dashboard.src.services.common.async_db import get_pool
from yosai_intel_dashboard.src.services.security import require_permission
from yosai_intel_dashboard.src.services.websocket_server import AnalyticsWebSocketServer
from yosai_intel_dashboard.src.infrastructure.discovery.health_check import (
    register_health_check,
    setup_health_checks,
)
from shared.errors.types import ErrorCode, ErrorResponse

from yosai_intel_dashboard.src.services.intel_analysis_service.core import (
    cluster_users_by_coaccess,
    detect_behavioral_deviations,
    detect_power_structures,
    find_unusual_collaborations,
    propagate_risk,
)
from yosai_intel_dashboard.src.infrastructure.callbacks import (
    CallbackType,
    register_callback,
    unregister_callback,
)
from shared.models.analytics import (
    AccessLogRequest,
    ReportRequest,
    RiskPropagationRequest,
    SocialNetworkRequest,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application setup
# ---------------------------------------------------------------------------

cache_manager = InMemoryCacheManager(CacheConfig(timeout_seconds=300))
registry.register("cached_analytics_service", CachedAnalyticsService(cache_manager))
ws_server: AnalyticsWebSocketServer | None = None

app = FastAPI(dependencies=[Depends(require_permission("analytics.read"))])


async def _database_health(_: FastAPI) -> Dict[str, Any]:
    try:
        pool = await get_pool()
        healthy = pool is not None
    except Exception:  # pragma: no cover - best effort
        healthy = False
    return {"healthy": healthy, "circuit_breaker": "closed", "retries": 0}


def _broker_health(_: FastAPI) -> Dict[str, Any]:
    return {"healthy": True, "circuit_breaker": "closed", "retries": 0}


def _external_api_health(_: FastAPI) -> Dict[str, Any]:
    return {"healthy": True, "circuit_breaker": "closed", "retries": 0}


register_health_check(app, "database", _database_health)
register_health_check(app, "message_broker", _broker_health)
register_health_check(app, "external_api", _external_api_health)
setup_health_checks(app)


ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "Bad Request"},
    401: {"model": ErrorResponse, "description": "Unauthorized"},
    404: {"model": ErrorResponse, "description": "Not Found"},
    500: {"model": ErrorResponse, "description": "Internal Server Error"},
}


async def get_service() -> CachedAnalyticsService:
    """Return the analytics service instance."""
    return registry.get("cached_analytics_service")


@app.on_event("startup")
async def _startup() -> None:
    global ws_server
    await cache_manager.start()
    ws_server = AnalyticsWebSocketServer()


@app.on_event("shutdown")
async def _shutdown() -> None:
    await cache_manager.stop()
    if ws_server is not None:
        ws_server.stop()


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


@app.get("/api/v1/analytics/patterns", responses=ERROR_RESPONSES)
async def get_patterns_analysis(
    query: AnalyticsQuery = Depends(),
    service: CachedAnalyticsService = Depends(get_service),
):
    data = await service.get_analytics_summary(query.facility_id, query.range)
    return JSONResponse(content=data)


@app.get("/api/v1/analytics/sources", responses=ERROR_RESPONSES)
async def get_data_sources() -> JSONResponse:
    return JSONResponse(
        content={"sources": [{"value": "test", "label": "Test Data Source"}]}
    )


@app.get("/api/v1/analytics/health", responses=ERROR_RESPONSES)
async def analytics_health() -> JSONResponse:
    return JSONResponse(content={"status": "healthy", "service": "minimal"})


@app.get("/api/v1/analytics/chart/{chart_type}", responses=ERROR_RESPONSES)
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
    raise http_error(ErrorCode.INVALID_INPUT, "Unknown chart type", 400)


@app.get("/api/v1/export/analytics/json", responses=ERROR_RESPONSES)
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


@app.get("/api/v1/export/formats", responses=ERROR_RESPONSES)
async def get_export_formats() -> JSONResponse:
    formats = [
        {"type": "csv", "name": "CSV", "description": "Comma-separated values"},
        {"type": "json", "name": "JSON", "description": "JavaScript Object Notation"},
        {"type": "xlsx", "name": "Excel", "description": "Microsoft Excel format"},
    ]
    return JSONResponse(content={"formats": formats})


@app.get("/api/v1/analytics/all", responses=ERROR_RESPONSES)
async def get_all_analytics(
    query: AnalyticsQuery = Depends(),
    service: CachedAnalyticsService = Depends(get_service),
):
    data = await service.get_analytics_summary(query.facility_id, query.range)
    return JSONResponse(content=data)


@app.post("/api/v1/analytics/report", responses=ERROR_RESPONSES)
async def generate_report(
    req: ReportRequest,
    _: None = Depends(require_permission("analytics.read")),
):
    """Generate an analytics report asynchronously."""
    service = get_analytics_service()
    if service is None:
        raise http_error(ErrorCode.UNAVAILABLE, "analytics service unavailable", 503)

    report = await asyncio.to_thread(
        service.generate_report,
        req.type,
        {"timeframe": req.timeframe, **(req.params or {})},
    )

    if req.format == "file":
        body = json.dumps(report, indent=2)
        headers = {
            "Content-Disposition": f"attachment; filename={req.type}_report.json"
        }
        return StreamingResponse(
            iter([body]), media_type="application/json", headers=headers
        )

    return JSONResponse(content=report)


@app.post("/api/v1/investigate/social-network", responses=ERROR_RESPONSES)
async def investigate_social_network(req: SocialNetworkRequest) -> JSONResponse:
    """Analyse interactions to uncover power structures and unusual links."""

    power = detect_power_structures(req.interactions)
    unusual = find_unusual_collaborations(
        req.interactions, min_occurrences=req.min_occurrences
    )
    return JSONResponse(content={"power": power, "unusual": [list(p) for p in unusual]})


@app.post("/api/v1/investigate/cliques", responses=ERROR_RESPONSES)
async def investigate_cliques(req: AccessLogRequest) -> JSONResponse:
    """Cluster users by co-access patterns and flag deviations."""

    clusters = cluster_users_by_coaccess(req.records)
    deviations = detect_behavioral_deviations(req.records, clusters)
    clusters_serialisable = {
        "|".join(sorted(k)): sorted(v) for k, v in clusters.items()
    }
    deviations_serialisable = {user: sorted(res) for user, res in deviations.items()}
    return JSONResponse(
        content={
            "clusters": clusters_serialisable,
            "deviations": deviations_serialisable,
        }
    )


@app.post("/api/v1/investigate/risk", responses=ERROR_RESPONSES)
async def investigate_risk(req: RiskPropagationRequest) -> JSONResponse:
    """Propagate risk scores through a trust network."""

    risks = propagate_risk(
        req.base_risks,
        req.links,
        iterations=req.iterations,
        decay=req.decay,
    )
    return JSONResponse(content={"risks": risks})


# ---------------------------------------------------------------------------
# Real-time update feeds
# ---------------------------------------------------------------------------


@app.websocket("/api/v1/ws/analytics")
async def analytics_ws(websocket: WebSocket) -> None:
    await websocket.accept()
    queue: asyncio.Queue[str] = asyncio.Queue()

    def _handler(payload: dict) -> None:
        queue.put_nowait(json.dumps(payload))

    register_callback(
        CallbackType.ANALYTICS_UPDATE,
        _handler,
        component_id="analytics_ws",
    )
    try:
        while True:
            msg = await queue.get()
            await websocket.send_text(msg)
    except WebSocketDisconnect:
        pass
    finally:
        unregister_callback(CallbackType.ANALYTICS_UPDATE, _handler)


@app.get("/api/v1/sse/analytics")
async def analytics_sse() -> StreamingResponse:
    queue: asyncio.Queue[str] = asyncio.Queue()

    def _handler(payload: dict) -> None:
        queue.put_nowait(json.dumps(payload))

    register_callback(
        CallbackType.ANALYTICS_UPDATE,
        _handler,
        component_id="analytics_sse",
    )

    async def _generator() -> AsyncIterator[str]:
        try:
            while True:
                data = await queue.get()
                yield f"data: {data}\n\n"
        finally:
            unregister_callback(CallbackType.ANALYTICS_UPDATE, _handler)

    return StreamingResponse(_generator(), media_type="text/event-stream")


__all__ = ["app", "get_service", "ws_server"]
