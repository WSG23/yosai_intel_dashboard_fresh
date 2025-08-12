from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.status import HTTP_413_REQUEST_ENTITY_TOO_LARGE


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests exceeding a maximum body size."""

    def __init__(self, app, max_bytes: int) -> None:
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request, call_next):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_bytes:
            return Response(status_code=HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        body = await request.body()
        if len(body) > self.max_bytes:
            return Response(status_code=HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        request._body = body
        return await call_next(request)
