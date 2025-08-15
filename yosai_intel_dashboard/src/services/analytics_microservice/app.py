"""FastAPI application for the analytics microservice used in tests.

The original project exposes a rich set of endpoints and relies on several
infrastructure components.  For the purposes of the kata environment we only
need a very small subset of that functionality.  This module provides a
light‑weight implementation that is sufficient for the unit tests while keeping
the public API similar to the real service.
"""

from __future__ import annotations

from typing import Dict
import os

from fastapi import Depends, FastAPI

from yosai_intel_dashboard.src.services.analytics_service import (
    create_analytics_service,
)
from tracing import init_tracing
from ..common.service_discovery import ConsulServiceDiscovery

try:  # pragma: no cover - optional dependency in tests
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
except Exception:  # pragma: no cover - instrumentation is optional
    FastAPIInstrumentor = None  # type: ignore

try:  # pragma: no cover - optional dependency in tests
    from prometheus_fastapi_instrumentator import Instrumentator
except Exception:  # pragma: no cover - instrumentation is optional
    Instrumentator = None  # type: ignore

try:
    # Prefer the real security utilities when they are available.
    from yosai_intel_dashboard.src.core.security import (
        rate_limit_decorator,
        verify_token,
    )
except Exception:  # pragma: no cover - fall back to local stubs
    from .security import rate_limit_decorator, verify_token


app = FastAPI()

# Instrumentation.  These libraries are optional and may be replaced by
# test doubles, so we guard their use with runtime checks.
if FastAPIInstrumentor is not None:
    FastAPIInstrumentor.instrument_app(app)
if Instrumentator is not None:
    Instrumentator().instrument(app).expose(app)

# Initialise tracing for the service.
init_tracing("analytics-microservice")

# Resolve dependent service locations dynamically at runtime.
_discovery = ConsulServiceDiscovery()


@app.on_event("startup")
async def _configure_discovery() -> None:
    if addr := _discovery.get_service("analytics-db"):
        os.environ.setdefault("DATABASE_URL", f"postgresql://{addr}/analytics")


# Create the analytics service once on startup.  The tests provide a stub for
# ``create_analytics_service`` so no heavy initialisation happens here.
service = create_analytics_service()


@app.get("/api/v1/analytics/dashboard-summary")
async def dashboard_summary(_: dict = Depends(verify_token)) -> Dict[str, object]:
    """Return a summary of analytics data."""
    return service.get_dashboard_summary()


@app.get("/api/v1/analytics/access-patterns")
@rate_limit_decorator()
async def access_patterns(
    days: int = 7,
    _: dict = Depends(verify_token),
) -> Dict[str, object]:
    """Return access pattern analytics.

    Parameters
    ----------
    days:
        Number of days to include in the analysis.  Defaults to ``7``.
    """

    data = service.get_access_patterns_analysis(days=days)
    data.setdefault("page", 1)
    data.setdefault("size", 50)
    return data


__all__ = ["app"]
