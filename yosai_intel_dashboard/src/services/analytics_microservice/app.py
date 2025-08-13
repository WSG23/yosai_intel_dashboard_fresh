from __future__ import annotations

"""Minimal FastAPI application for analytics microservice."""

from typing import Dict

from fastapi import Depends, FastAPI

from .analytics_service import AnalyticsService, get_analytics_service

app = FastAPI()


@app.on_event("startup")  # type: ignore[misc]

async def _startup() -> None:
    """Placeholder startup hook."""
    return None


@app.get("/api/v1/health")  # type: ignore[misc]
async def health() -> Dict[str, str]:
    """Basic service health endpoint."""
    return {"status": "ok"}


@app.get("/api/v1/analytics/dashboard-summary")  # type: ignore[misc]
async def dashboard_summary(

    svc: AnalyticsService = Depends(get_analytics_service),
) -> Dict[str, str]:
    """Return placeholder dashboard summary."""
    data = svc.get_analytics("dashboard")
    return {"status": data["status"]}
