from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from api.middleware.body_size_limit import BodySizeLimitMiddleware
from api.middleware.security_headers import SecurityHeadersMiddleware

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
async def echo(body: EchoRequest) -> EchoResponse:
    return EchoResponse(message=body.message)
