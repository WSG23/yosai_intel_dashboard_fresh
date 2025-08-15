from __future__ import annotations

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from services.api.middleware.body_size_limit import BodySizeLimitMiddleware
from services.api.middleware.security_headers import SecurityHeadersMiddleware
from yosai_intel_dashboard.src.services.security import requires_role

app = FastAPI()
app.add_middleware(BodySizeLimitMiddleware, max_bytes=50 * 1024 * 1024)
app.add_middleware(SecurityHeadersMiddleware)


@app.route("/health")
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


class EchoRequest(BaseModel):
    message: str


class EchoResponse(BaseModel):
    message: str


@app.post("/api/v1/echo", response_model=EchoResponse)
async def echo(
    body: EchoRequest, _: None = Depends(requires_role("admin"))
) -> EchoResponse:
    return EchoResponse(message=body.message)
