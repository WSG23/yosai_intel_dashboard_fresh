from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import PlainTextResponse


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    """Reject requests with bodies exceeding the configured limit."""

    def __init__(self, app, max_bytes: int = 50 * 1024 * 1024):
        super().__init__(app)
        self.max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next):
        """Return 413 if the request body is too large."""
        if request.method in {"POST", "PUT", "PATCH"}:
            cl = request.headers.get("content-length")
            if cl is not None:
                try:
                    if int(cl) > self.max_bytes:
                        return PlainTextResponse("Payload too large", status_code=413)
                except ValueError:
                    pass
        return await call_next(request)
