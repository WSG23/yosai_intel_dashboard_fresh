import asyncio
from fastapi import FastAPI, Header, HTTPException, status, Depends
from shared.errors.types import ErrorCode
from yosai_framework.errors import ServiceError
from yosai_framework.service import BaseService

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator

import importlib.util
import pathlib
import sys
import os

try:
    from services.streaming import StreamingService
except ModuleNotFoundError:
    spec = importlib.util.spec_from_file_location(
        "services.streaming",
        pathlib.Path(__file__).resolve().parents[1] / "streaming" / "service.py",
    )
    streaming_mod = importlib.util.module_from_spec(spec)
    sys.modules["services.streaming"] = streaming_mod
    if spec.loader:
        spec.loader.exec_module(streaming_mod)
    StreamingService = streaming_mod.StreamingService
try:
    from services.security import verify_service_jwt
except ModuleNotFoundError:
    spec = importlib.util.spec_from_file_location(
        "services.security",
        pathlib.Path(__file__).resolve().parents[1] / "security" / "__init__.py",
    )
    security_mod = importlib.util.module_from_spec(spec)
    sys.modules["services.security"] = security_mod
    if spec.loader:
        spec.loader.exec_module(security_mod)
    verify_service_jwt = security_mod.verify_service_jwt
from tracing import trace_async_operation

SERVICE_NAME = "event-ingestion-service"
os.environ.setdefault("YOSAI_SERVICE_NAME", SERVICE_NAME)
CONFIG_PATH = pathlib.Path(__file__).with_name("service_config.yaml")
service_base = BaseService(SERVICE_NAME, str(CONFIG_PATH))
app = service_base.app
try:
    service = StreamingService()
except Exception:
    service = None


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
