from fastapi import FastAPI, HTTPException, Request, status
from pydantic import BaseModel
import asyncio
from typing import Dict, Any

from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_fastapi_instrumentator import Instrumentator

from tracing import init_tracing

from services.security import AuthenticationService, ServiceTokenManager
from fastapi.responses import JSONResponse

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


@app.post("/analyze")
async def analyze(request: AnalyticsRequest):
    from services.analytics_service import AnalyticsService

    service = AnalyticsService()
    loop = asyncio.get_event_loop()
    try:
        result = await loop.run_in_executor(
            None, service.process_request, request.dict()
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


FastAPIInstrumentor.instrument_app(app)
Instrumentator().instrument(app).expose(app)
