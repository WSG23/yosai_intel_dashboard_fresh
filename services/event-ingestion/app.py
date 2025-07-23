import asyncio
from fastapi import FastAPI, Header, HTTPException, status, Depends
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator

from services.streaming import StreamingService
from services.security import verify_service_jwt
from tracing import trace_async_operation, init_tracing, configure_logging

SERVICE_NAME = "event-ingestion-service"
init_tracing(SERVICE_NAME)
configure_logging(SERVICE_NAME)

app = FastAPI(title="Event Ingestion Service")
service = StreamingService()


def verify_token(authorization: str = Header("")) -> None:
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized"
        )
    token = authorization.split(" ", 1)[1]
    if not verify_service_jwt(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized"
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


@app.on_event("shutdown")
async def shutdown() -> None:
    service.close()


@app.get("/health")
async def health(_: None = Depends(verify_token)) -> dict:
    return service.health_check()


FastAPIInstrumentor.instrument_app(app)
Instrumentator().instrument(app).expose(app)
