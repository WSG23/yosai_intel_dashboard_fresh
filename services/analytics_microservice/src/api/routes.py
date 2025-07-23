from __future__ import annotations

import logging
import os
import time

from fastapi import Depends, FastAPI, Header, HTTPException, status
from jose import jwt
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel

from .middleware import setup_metrics
from ..core.dependencies import container
from services.analytics_microservice import async_queries
from services.common import async_db
from tracing import init_tracing

init_tracing("analytics-microservice")

app = FastAPI(title="Analytics Microservice")

PLACEHOLDER_JWT_SECRET = "change-me"
JWT_SECRET = os.getenv("JWT_SECRET", PLACEHOLDER_JWT_SECRET)
if JWT_SECRET == PLACEHOLDER_JWT_SECRET:
    logging.warning("JWT_SECRET environment variable not set; using placeholder")


def verify_token(authorization: str = Header("")) -> None:
    """Validate Authorization header using JWT_SECRET."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized"
        )
    token = authorization.split(" ", 1)[1]
    try:
        claims = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized"
        ) from exc
    exp = claims.get("exp")
    if exp is not None and exp < time.time():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized"
        )
    if not claims.get("iss"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized"
        )


class PatternsRequest(BaseModel):
    days: int = 7


@app.on_event("startup")
async def _startup() -> None:
    if JWT_SECRET == PLACEHOLDER_JWT_SECRET:
        raise RuntimeError("JWT_SECRET environment variable not set")
    await container.init_resources()
    app.state.ready = True
    app.state.startup_complete = True
    app.state.live = True


@app.on_event("shutdown")
async def _shutdown() -> None:
    await container.shutdown_resources()
    app.state.ready = False
    app.state.live = False


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/health/live")
async def health_live() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/health/startup")
async def health_startup() -> dict[str, str]:
    """Startup probe."""
    if app.state.startup_complete:
        return {"status": "complete"}
    raise HTTPException(status_code=503, detail="starting")


@app.get("/health/ready")
async def health_ready() -> dict[str, str]:
    """Readiness probe."""
    if app.state.ready:
        return {"status": "ready"}
    raise HTTPException(status_code=503, detail="not ready")


@app.post("/api/v1/analytics/get_dashboard_summary")
async def dashboard_summary(_: None = Depends(verify_token)):
    pool = await async_db.get_pool()
    return await async_queries.fetch_dashboard_summary(pool)


@app.post("/api/v1/analytics/get_access_patterns_analysis")
async def access_patterns(req: PatternsRequest, _: None = Depends(verify_token)):
    pool = await async_db.get_pool()
    return await async_queries.fetch_access_patterns(pool, req.days)


FastAPIInstrumentor.instrument_app(app)
setup_metrics(app)
