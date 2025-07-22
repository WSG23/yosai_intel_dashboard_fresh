import asyncio
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator

from services.streaming import StreamingService
from tracing import trace_async_operation

app = FastAPI(title="Event Ingestion Service")
service = StreamingService()

async def _consume_loop() -> None:
    while True:
        for msg in service.consume(timeout=1.0):
            app.logger.info("received %s", msg)
        await asyncio.sleep(0.1)

@app.on_event("startup")
async def startup() -> None:
    service.initialize()
    asyncio.create_task(trace_async_operation("consume_loop", "ingest", _consume_loop()))

@app.on_event("shutdown")
async def shutdown() -> None:
    service.close()

@app.get("/health")
async def health() -> dict:
    return service.health_check()

FastAPIInstrumentor.instrument_app(app)
Instrumentator().instrument(app).expose(app)
