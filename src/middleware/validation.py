import asyncio
from typing import Dict, Optional, Type

from pydantic import BaseModel, ValidationError
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class ValidationMiddleware(BaseHTTPMiddleware):
    """Validate request data and optionally enforce rate limits.

    Parameters
    ----------
    app:
        The ASGI application.
    query_model:
        Optional Pydantic model used to validate query parameters.
    body_model:
        Optional Pydantic model used to validate request bodies.
    limiter:
        Rate limiter instance providing a ``hit(user, ip)`` method.
    min_interval:
        Minimum interval between requests from the same IP for basic
        throttling.
    """

    def __init__(
        self,
        app,
        *,
        query_model: Optional[Type[BaseModel]] = None,
        body_model: Optional[Type[BaseModel]] = None,
        limiter: Optional[object] = None,
        min_interval: float = 0.0,
    ) -> None:
        super().__init__(app)
        self.query_model = query_model
        self.body_model = body_model
        self.limiter = limiter
        self.min_interval = min_interval
        self._last_request: Dict[str, float] = {}

    async def dispatch(self, request: Request, call_next) -> Response:
        identifier = request.client.host if request.client else "unknown"
        headers: Dict[str, str] = {}

        if self.limiter is not None:
            result = await asyncio.to_thread(self.limiter.hit, identifier, identifier)
            headers = {
                "X-RateLimit-Limit": str(result.get("limit", 0)),
                "X-RateLimit-Remaining": str(result.get("remaining", 0)),
            }
            if not result.get("allowed", True):
                retry = result.get("retry_after")
                if retry is not None:
                    headers["Retry-After"] = str(int(retry))
                return JSONResponse(
                    {"detail": "rate limit exceeded"}, status_code=429, headers=headers
                )

        if self.min_interval > 0:
            last = self._last_request.get(identifier, 0.0)
            now = asyncio.get_event_loop().time()
            wait = self.min_interval - (now - last)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_request[identifier] = asyncio.get_event_loop().time()

        try:
            if self.query_model:
                self.query_model(**dict(request.query_params))
            if (
                self.body_model
                and request.method in {"POST", "PUT", "PATCH", "DELETE"}
            ):
                data = await request.json()
                self.body_model(**data)
        except ValidationError as exc:  # pragma: no cover - simple error path
            return JSONResponse({"detail": exc.errors()}, status_code=422)

        response = await call_next(request)
        for k, v in headers.items():
            response.headers[k] = v
        return response
