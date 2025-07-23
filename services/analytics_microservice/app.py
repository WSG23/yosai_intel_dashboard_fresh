import logging
import os
import time

from fastapi import Depends, Header, HTTPException, status
from yosai_framework.service import BaseService
from shared.errors.types import ErrorCode
from yosai_framework.errors import ServiceError
from jose import jwt
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

from config import get_database_config
from config.validate import validate_required_env
from services.analytics_microservice import async_queries
from services.common.async_db import close_pool, create_pool, get_pool


SERVICE_NAME = "analytics-microservice"
service = BaseService(SERVICE_NAME, "")
app = service.app

PLACEHOLDER_JWT_SECRET = "change-me"
JWT_SECRET = os.getenv("JWT_SECRET", PLACEHOLDER_JWT_SECRET)
if JWT_SECRET == PLACEHOLDER_JWT_SECRET:
    logging.warning("JWT_SECRET environment variable not set; using placeholder")


def verify_token(authorization: str = Header("")) -> None:
    """Validate Authorization header using JWT_SECRET."""
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ServiceError(ErrorCode.UNAUTHORIZED, "unauthorized").to_dict(),
        )
    token = authorization.split(" ", 1)[1]
    try:
        claims = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ServiceError(ErrorCode.UNAUTHORIZED, "unauthorized").to_dict(),
        ) from exc
    exp = claims.get("exp")
    if exp is not None and exp < time.time():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ServiceError(ErrorCode.UNAUTHORIZED, "unauthorized").to_dict(),
        )
    if not claims.get("iss"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ServiceError(ErrorCode.UNAUTHORIZED, "unauthorized").to_dict(),
        )


class PatternsRequest(BaseModel):
    days: int = 7


@app.on_event("startup")
async def _startup() -> None:
    validate_required_env(["JWT_SECRET"])
    if JWT_SECRET == PLACEHOLDER_JWT_SECRET:
        raise RuntimeError("JWT_SECRET environment variable not set")

    cfg = get_database_config()
    await create_pool(
        cfg.get_connection_string(),
        min_size=cfg.initial_pool_size,
        max_size=cfg.max_pool_size,
        timeout=cfg.connection_timeout,
    )

    # Redis or other dependencies would be initialized here
    app.state.ready = True
    app.state.startup_complete = True


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/health/live")
async def health_live() -> dict[str, str]:
    """Liveness probe."""
    return {"status": "ok" if app.state.live else "shutdown"}


@app.get("/health/startup")
async def health_startup() -> dict[str, str]:
    """Startup probe."""
    if app.state.startup_complete:
        return {"status": "complete"}
    raise HTTPException(
        status_code=503,
        detail=ServiceError(ErrorCode.UNAVAILABLE, "starting").to_dict(),
    )


@app.get("/health/ready")
async def health_ready() -> dict[str, str]:
    """Readiness probe."""
    if app.state.ready:
        return {"status": "ready"}
    raise HTTPException(
        status_code=503,
        detail=ServiceError(ErrorCode.UNAVAILABLE, "not ready").to_dict(),
    )



@app.on_event("shutdown")
async def _shutdown() -> None:
    await close_pool()
    service.stop()


@app.post("/api/v1/analytics/get_dashboard_summary")
async def dashboard_summary(_: None = Depends(verify_token)):
    pool = await get_pool()
    return await async_queries.fetch_dashboard_summary(pool)


@app.post("/api/v1/analytics/get_access_patterns_analysis")
async def access_patterns(req: PatternsRequest, _: None = Depends(verify_token)):
    pool = await get_pool()
    return await async_queries.fetch_access_patterns(pool, req.days)


FastAPIInstrumentor.instrument_app(app)
Instrumentator().instrument(app).expose(app)
