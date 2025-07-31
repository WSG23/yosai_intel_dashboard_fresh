"""Reusable FastAPI health check utilities."""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, Dict

from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from yosai_intel_dashboard.src.error_handling import http_error
from shared.errors.types import ErrorCode

HealthCheck = Callable[[FastAPI], Awaitable[bool] | bool]

router = APIRouter()


@router.get("/health")
async def health(request: Request) -> JSONResponse:
    checks: Dict[str, bool] = getattr(request.app.state, "dependency_health", {})
    status = "ok" if all(checks.values()) else "degraded"
    return JSONResponse({"status": status, "dependencies": checks})


@router.get("/health/live")
async def health_live(request: Request) -> JSONResponse:
    status = "ok" if getattr(request.app.state, "live", True) else "shutdown"
    return JSONResponse({"status": status})


@router.get("/health/startup")
async def health_startup(request: Request) -> JSONResponse:
    if getattr(request.app.state, "startup_complete", False):
        return JSONResponse({"status": "complete"})
    raise http_error(ErrorCode.UNAVAILABLE, "starting", 503)


@router.get("/health/ready")
async def health_ready(request: Request) -> JSONResponse:
    checks: Dict[str, bool] = getattr(request.app.state, "dependency_health", {})
    ready = getattr(request.app.state, "ready", False)
    healthy = ready and all(checks.values())
    if healthy:
        return JSONResponse({"status": "ready", "dependencies": checks})
    raise http_error(ErrorCode.UNAVAILABLE, "not ready", 503)


class DependencyHealthMiddleware(BaseHTTPMiddleware):
    """Middleware aggregating dependency health status."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        if not hasattr(app.state, "health_checks"):
            app.state.health_checks: Dict[str, HealthCheck] = {}
        app.state.dependency_health = {}

    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/health"):
            results: Dict[str, bool] = {}
            for name, func in request.app.state.health_checks.items():
                try:
                    res = func(request.app)
                    if asyncio.iscoroutine(res):
                        res = await res
                    results[name] = bool(res)
                except Exception:
                    results[name] = False
            request.app.state.dependency_health = results
        return await call_next(request)


def register_health_check(app: FastAPI, name: str, func: HealthCheck) -> None:
    """Register a dependency health check function."""
    if not hasattr(app.state, "health_checks"):
        app.state.health_checks = {}
    app.state.health_checks[name] = func


def setup_health_checks(app: FastAPI) -> None:
    """Attach health router and middleware to *app*."""
    app.add_middleware(DependencyHealthMiddleware)
    app.include_router(router)
