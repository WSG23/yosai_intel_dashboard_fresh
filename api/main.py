from __future__ import annotations

from fastapi import FastAPI, Request, Response

from api.middleware.body_size_limit import BodySizeLimitMiddleware
from api.middleware.security_headers import SecurityHeadersMiddleware


app = FastAPI()
app.add_middleware(BodySizeLimitMiddleware, max_bytes=50 * 1024 * 1024)
app.add_middleware(SecurityHeadersMiddleware)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/echo")
async def echo(request: Request) -> Response:
    data = await request.body()
    return Response(content=data, media_type="application/octet-stream")
