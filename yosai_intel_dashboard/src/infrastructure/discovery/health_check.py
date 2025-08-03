from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict
import inspect

from fastapi import APIRouter, FastAPI

health_check_router = APIRouter()


def health_check() -> APIRouter:
    """Factory returning the health check router."""
    return health_check_router


def register_health_check(
    app: FastAPI, name: str, check: Callable[[FastAPI], Awaitable[bool] | bool]
) -> None:
    """Register a health check function for the service.

    The callable can be synchronous or asynchronous and receives the ``FastAPI``
    application instance. Results are stored in ``app.state.health_checks``.
    """
    checks: Dict[str, Callable[[FastAPI], Awaitable[bool] | bool]] = getattr(
        app.state, "health_checks", {}
    )
    checks[name] = check
    app.state.health_checks = checks


def setup_health_checks(app: FastAPI) -> None:
    """Attach an endpoint that exposes registered health checks."""

    @health_check_router.get("/health/services")
    async def _health_services() -> Dict[str, bool]:
        results: Dict[str, bool] = {}
        checks = getattr(app.state, "health_checks", {})
        for key, func in checks.items():
            try:
                if inspect.iscoroutinefunction(func):
                    results[key] = bool(await func(app))
                else:
                    results[key] = bool(func(app))
            except Exception:
                results[key] = False
        return results

    app.include_router(health_check_router)


__all__ = ["health_check_router", "health_check", "register_health_check", "setup_health_checks"]
