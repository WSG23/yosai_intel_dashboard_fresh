"""FastAPI middleware for unified error responses."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .api_error_response import serialize_error
from .core import ErrorHandler
from .exceptions import ErrorCategory


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Transform uncaught exceptions into standard error responses."""

    def __init__(self, app: FastAPI, handler: ErrorHandler | None = None) -> None:
        super().__init__(app)
        self.handler = handler or ErrorHandler()

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        try:
            return await call_next(request)
        except Exception as exc:  # noqa: BLE001
            payload, status = serialize_error(
                exc, ErrorCategory.INTERNAL, handler=self.handler
            )
            return JSONResponse(content=payload, status_code=status)

    @classmethod
    def setup(cls, app: FastAPI, handler: ErrorHandler | None = None) -> None:
        """Add the middleware to *app* and document the error schema."""
        app.add_middleware(cls, handler=handler)


__all__ = ["ErrorHandlingMiddleware"]
