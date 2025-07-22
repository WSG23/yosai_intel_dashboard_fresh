from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator
from pydantic import BaseModel

from config import get_database_config
from services.analytics_microservice import async_queries
from services.common.async_db import create_pool, get_pool
from services.security import AuthenticationService, ServiceTokenManager
from tracing import init_tracing

init_tracing("analytics-service")

app = FastAPI(title="Analytics Service")

token_manager = ServiceTokenManager()
auth_service = AuthenticationService(token_manager)


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return JSONResponse(
            {"detail": "unauthorized"}, status_code=status.HTTP_401_UNAUTHORIZED
        )
    token = auth.split(" ", 1)[1]
    if not auth_service.authenticate(token):
        return JSONResponse(
            {"detail": "unauthorized"}, status_code=status.HTTP_401_UNAUTHORIZED
        )
    return await call_next(request)


class AnalyticsRequest(BaseModel):
    query_type: str
    parameters: Dict[str, Any]


@app.on_event("startup")
async def _startup() -> None:
    cfg = get_database_config()
    await create_pool(
        cfg.get_connection_string(),
        min_size=cfg.initial_pool_size,
        max_size=cfg.max_pool_size,
        timeout=cfg.connection_timeout,
    )


@app.post("/analyze")
async def analyze(request: AnalyticsRequest):
    pool = await get_pool()
    try:
        if request.query_type == "summary":
            return await async_queries.fetch_dashboard_summary(
                pool, **request.parameters
            )
        if request.query_type == "patterns":
            days = int(request.parameters.get("days", 7))
            return await async_queries.fetch_access_patterns(pool, days)
        raise HTTPException(status_code=400, detail="invalid query_type")
    except Exception as e:  # pragma: no cover - best effort
        raise HTTPException(status_code=500, detail=str(e)) from e


FastAPIInstrumentor.instrument_app(app)
Instrumentator().instrument(app).expose(app)
