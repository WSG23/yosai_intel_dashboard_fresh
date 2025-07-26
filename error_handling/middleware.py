"""FastAPI middleware for unified error responses."""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from shared.errors.types import ErrorCode
from yosai_framework.errors import CODE_TO_STATUS
from core.exceptions import ValidationError

from .core import ErrorHandler
from .exceptions import ErrorCategory


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Transform uncaught exceptions into standard error responses."""

    def __init__(self, app, handler: ErrorHandler | None = None) -> None:
        super().__init__(app)
        self.handler = handler or ErrorHandler()

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        try:
            return await call_next(request)
        except Exception as exc:  # noqa: BLE001
            if isinstance(exc, ValidationError):
                body = {
                    "code": exc.code,
                    "message": exc.message,
                    "field": exc.field,
                }
                status = CODE_TO_STATUS.get(ErrorCode.INVALID_INPUT, 400)
                return JSONResponse(content=body, status_code=status)
            err = self.handler.handle(exc, ErrorCategory.INTERNAL)
            status = CODE_TO_STATUS.get(ErrorCode(err.category.value), 500)
            return JSONResponse(content=err.to_dict(), status_code=status)


__all__ = ["ErrorHandlingMiddleware"]
