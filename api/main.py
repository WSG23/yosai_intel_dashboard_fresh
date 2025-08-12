from __future__ import annotations

from starlette.applications import Starlette
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse, JSONResponse, Response

MAX_PAYLOAD_SIZE = 50 * 1024 * 1024  # 50 MB


class PayloadLimitMiddleware(BaseHTTPMiddleware):
    """Middleware enforcing a maximum request payload size."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        content_length = request.headers.get("content-length")
        if content_length is not None and int(content_length) > MAX_PAYLOAD_SIZE:
            return PlainTextResponse("Payload too large", status_code=413)
        return await call_next(request)


app = Starlette()


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


app.add_middleware(PayloadLimitMiddleware)


@app.route("/health")
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.route("/echo", methods=["POST"])
async def echo(request: Request) -> Response:
    data = await request.body()
    return Response(content=data, media_type="application/octet-stream")
