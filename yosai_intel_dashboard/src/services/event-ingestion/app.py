from __future__ import annotations

import asyncio
import json
import os
import pathlib

from fastapi import Header, status
from fastapi.openapi.utils import get_openapi
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator

from yosai_intel_dashboard.src.infrastructure.config.config_loader import load_service_config
import redis
from middleware.rate_limit import RateLimitMiddleware, RedisRateLimiter
from yosai_intel_dashboard.src.error_handling import http_error
from yosai_intel_dashboard.src.error_handling.middleware import ErrorHandlingMiddleware
from yosai_intel_dashboard.src.services.security import verify_service_jwt
from yosai_intel_dashboard.src.services.streaming.service import StreamingService
from shared.errors.types import ErrorCode
from tracing import trace_async_operation
from yosai_framework.errors import ServiceError
from yosai_framework.service import BaseService
from yosai_intel_dashboard.src.infrastructure.discovery.health_check import (
    register_health_check,
    setup_health_checks,
)

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

# Configure rate limiter
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))
rate_limiter = RedisRateLimiter(redis_client, {"default": {"limit": 100, "burst": 0}})
app.add_middleware(RateLimitMiddleware, limiter=rate_limiter)



def verify_token(authorization: str = Header("")) -> dict:
    if not authorization.startswith("Bearer "):
        raise http_error(
            ErrorCode.UNAUTHORIZED,
            "unauthorized",
            status.HTTP_401_UNAUTHORIZED,
        )
    token = authorization.split(" ", 1)[1]
    if not verify_service_jwt(token):
        raise http_error(
            ErrorCode.UNAUTHORIZED,
            "unauthorized",
            status.HTTP_401_UNAUTHORIZED,
        )


async def _consume_loop() -> None:
    while True:
        for msg in service.consume(timeout=1.0):
            app.logger.info("received %s", msg)
        await asyncio.sleep(0.1)


@app.on_event("startup")
async def startup() -> None:
    # Load environment driven settings
    load_service_config()
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
