from __future__ import annotations

import asyncio
import json
import os
import pathlib

from fastapi import Header, HTTPException, Request, status
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator

from core.security import RateLimiter
from error_handling.middleware import ErrorHandlingMiddleware
from yosai_intel_dashboard.src.infrastructure.discovery.health_check import (
    register_health_check,
    setup_health_checks,
)
from services.security import verify_service_jwt
from services.streaming.service import StreamingService
from shared.errors.types import ErrorCode
from tracing import trace_async_operation
from yosai_framework.errors import ServiceError
from yosai_framework.service import BaseService

SERVICE_NAME = "event-ingestion-service"
os.environ.setdefault("YOSAI_SERVICE_NAME", SERVICE_NAME)
CONFIG_PATH = pathlib.Path(__file__).with_name("service_config.yaml")
service_base = BaseService(SERVICE_NAME, str(CONFIG_PATH))
app = service_base.app
app.add_middleware(ErrorHandlingMiddleware)
try:
    service = StreamingService()
except Exception:
    service = None

register_health_check(app, "streaming", lambda _: service is not None)

rate_limiter = RateLimiter()


@app.middleware("http")
async def rate_limit(request: Request, call_next):
    auth = request.headers.get("Authorization", "")
    identifier = (
        auth.split(" ", 1)[1] if auth.startswith("Bearer ") else request.client.host
    )
    result = rate_limiter.is_allowed(identifier or "anonymous", request.client.host)
    if not result["allowed"]:
        headers = {}
        retry = result.get("retry_after")
        if retry:
            headers["Retry-After"] = str(int(retry))
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"detail": "rate limit exceeded"},
            headers=headers,
        )
    return await call_next(request)


def verify_token(authorization: str = Header("")) -> None:
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ServiceError(ErrorCode.UNAUTHORIZED, "unauthorized").to_dict(),
        )
    token = authorization.split(" ", 1)[1]
    if not verify_service_jwt(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ServiceError(ErrorCode.UNAUTHORIZED, "unauthorized").to_dict(),
        )


async def _consume_loop() -> None:
    while True:
        for msg in service.consume(timeout=1.0):
            app.logger.info("received %s", msg)
        await asyncio.sleep(0.1)


@app.on_event("startup")
async def startup() -> None:
    service.initialize()
    asyncio.create_task(
        trace_async_operation("consume_loop", "ingest", _consume_loop())
    )
    service_base.start()


@app.on_event("shutdown")
async def shutdown() -> None:
    service.close()
    service_base.stop()


FastAPIInstrumentor.instrument_app(app)
Instrumentator().instrument(app).expose(app)
setup_health_checks(app)


def custom_openapi() -> dict:
    """Add bearerAuth security scheme and Authorization header."""
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title=app.title,
        version="0.1.0",
        routes=app.routes,
    )
    components = schema.setdefault("components", {})
    security = components.setdefault("securitySchemes", {})
    security["bearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
    }
    for path in schema.get("paths", {}).values():
        for method in path.values():
            params = method.setdefault("parameters", [])
            if not any(p.get("name") == "authorization" for p in params):
                params.append(
                    {
                        "name": "authorization",
                        "in": "header",
                        "required": False,
                        "schema": {
                            "type": "string",
                            "default": "",
                            "title": "Authorization",
                        },
                    }
                )
            method.setdefault("security", [{"bearerAuth": []}])
    app.openapi_schema = schema
    return schema


app.openapi = custom_openapi


@app.on_event("startup")
async def _write_openapi() -> None:
    """Persist OpenAPI schema for docs."""
    docs_path = (
        pathlib.Path(__file__).resolve().parents[2]
        / "docs"
        / "event_ingestion_openapi.json"
    )
    docs_path.write_text(json.dumps(app.openapi(), indent=2))
