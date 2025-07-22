import time

from fastapi import Depends, FastAPI, Header, HTTPException, status
from jose import jwt
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

from config import get_database_config
from services.analytics_microservice import async_queries
from services.common.async_db import create_pool, get_pool
from tracing import init_tracing

init_tracing("analytics-microservice")

app = FastAPI(title="Analytics Microservice")


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


class PatternsRequest(BaseModel):
    days: int = 7


@app.on_event("startup")
async def _startup() -> None:
    cfg = get_database_config()
    await create_pool(
        cfg.get_connection_string(),
        min_size=cfg.initial_pool_size,
        max_size=cfg.max_pool_size,
        timeout=cfg.connection_timeout,
    )


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
