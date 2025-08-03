from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict
import inspect

from fastapi import APIRouter, FastAPI

health_check_router = APIRouter()


def health_check() -> APIRouter:
    """Factory returning the health check router."""
    return health_check_router


def register_health_check(
    app: FastAPI,
    name: str,
    check: Callable[[FastAPI], Awaitable[Dict[str, Any] | bool] | Dict[str, Any] | bool],
) -> None:
    """Register a health check function for the service.

    The callable can be synchronous or asynchronous and receives the ``FastAPI``
    application instance. Results are stored in ``app.state.health_checks``.
    Each callable should return either a boolean or a mapping with detailed
    health information. The returned mapping may contain keys such as
    ``healthy`` (bool), ``circuit_breaker`` (str) and ``retries`` (int).
    """
    checks: Dict[
        str, Callable[[FastAPI], Awaitable[Dict[str, Any] | bool] | Dict[str, Any] | bool]
    ] = getattr(app.state, "health_checks", {})
    checks[name] = check
    app.state.health_checks = checks


def setup_health_checks(app: FastAPI) -> None:
    """Attach endpoints that expose registered health checks and readiness."""

    # Remove any existing /health/ready route so our aggregated readiness handler
    # becomes authoritative.
    app.router.routes = [
        r
        for r in app.router.routes
        if not (getattr(r, "path", "") == "/health/ready" and "GET" in getattr(r, "methods", set()))
    ]

    @health_check_router.get("/health/services")
    async def _health_services() -> Dict[str, Dict[str, Any]]:
        """Return detailed health information for registered services."""

        results: Dict[str, Dict[str, Any]] = {}
        checks = getattr(app.state, "health_checks", {})
        for key, func in checks.items():
            try:
                if inspect.iscoroutinefunction(func):
                    value = await func(app)
                else:
                    value = func(app)
                default = {"healthy": bool(value), "circuit_breaker": "unknown", "retries": 0}
                if isinstance(value, dict):
                    default.update(value)
                    default["healthy"] = bool(value.get("healthy", value))
                results[key] = default
            except Exception as exc:  # pragma: no cover - best effort
                results[key] = {"healthy": False, "circuit_breaker": "open", "retries": 0, "error": str(exc)}
        return results

    @health_check_router.get("/health/ready")
    async def _health_ready() -> Dict[str, Any]:
        """Aggregate health checks into an overall readiness state."""

        services = await _health_services()
        ready = all(info.get("healthy", False) for info in services.values())
        return {"ready": ready, "services": services}

    app.include_router(health_check_router)


__all__ = ["health_check_router", "health_check", "register_health_check", "setup_health_checks"]
