"""FastAPI application for the analytics microservice used in tests.

The original project exposes a rich set of endpoints and relies on several
infrastructure components.  For the purposes of the kata environment we only
need a very small subset of that functionality.  This module provides a
light‑weight implementation that is sufficient for the unit tests while keeping
the public API similar to the real service.
"""

from __future__ import annotations

from typing import Any, Dict
import os
from time import perf_counter
import logging

from fastapi import Depends, FastAPI
from yosai_intel_dashboard.src.services.security import requires_role

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

try:  # pragma: no cover - optional dependency
    from prometheus_client import Histogram, Gauge

    _INFERENCE_LATENCY = Histogram(
        "inference_latency_seconds", "Latency of model predictions", ["model"]
    )
    _INFERENCE_ACCURACY = Gauge(
        "inference_accuracy", "Accuracy of model predictions", ["model"]
    )
except Exception:  # pragma: no cover - allow running without Prometheus
    _INFERENCE_LATENCY = None  # type: ignore
    _INFERENCE_ACCURACY = None  # type: ignore

try:
    # Prefer the real security utilities when they are available.
    from yosai_intel_dashboard.src.core.security import (
        rate_limit_decorator,
        verify_token,
    )
except Exception:  # pragma: no cover - fall back to local stubs
    from .security import rate_limit_decorator, verify_token


app = FastAPI()

logger = logging.getLogger(__name__)

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


def _run_prediction(
    model: Any, data: list[Any], actual: list[Any] | None = None
) -> tuple[Any, float]:
    """Execute ``model.predict`` recording latency and optional accuracy."""

    start = perf_counter()
    try:
        prediction = model.predict(data)
    except Exception:  # pragma: no cover - defensive
        logger.debug("Prediction failed", exc_info=True)
        return http_error(ErrorCode.INTERNAL)
    latency = perf_counter() - start
    try:
        if _INFERENCE_LATENCY is not None:
            _INFERENCE_LATENCY.labels(model.__class__.__name__).observe(latency)
    except Exception:  # pragma: no cover - metrics stub
        logger.debug("Latency metric recording failed")

    if actual is not None:
        try:
            total = len(actual)
            if total:
                correct = sum(1 for p, a in zip(prediction, actual) if p == a)
                metric = globals().get("_INFERENCE_ACCURACY")
                if metric is not None:
                    metric.labels(model.__class__.__name__).set(correct / total)
        except Exception:  # pragma: no cover - metrics stub
            logger.debug("Accuracy metric recording failed")

    return prediction, latency


@app.get("/api/v1/analytics/dashboard-summary")
async def dashboard_summary(
    _: dict = Depends(verify_token),
    __: None = Depends(requires_role("analyst")),
) -> Dict[str, object]:
    """Return a summary of analytics data."""
    return service.get_dashboard_summary()


@app.get("/api/v1/analytics/access-patterns")
@rate_limit_decorator()
async def access_patterns(
    days: int = 7,
    _: dict = Depends(verify_token),
    __: None = Depends(requires_role("analyst")),
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


__all__ = ["app", "_run_prediction"]
