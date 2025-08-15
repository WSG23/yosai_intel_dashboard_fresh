"""FastAPI middleware for unified error responses."""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from shared.errors.types import ErrorResponse

from .api_error_response import api_error_response
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
            payload, status = api_error_response(
                exc, ErrorCategory.INTERNAL, handler=self.handler
            )
            body = payload.get_json() if hasattr(payload, "get_json") else payload
            return JSONResponse(content=body, status_code=status)

    @classmethod
    def setup(cls, app: FastAPI, handler: ErrorHandler | None = None) -> None:
        """Add the middleware to *app* and document the error schema."""
        app.add_middleware(cls, handler=handler)
        _ensure_error_schema(app)


def _ensure_error_schema(app: FastAPI) -> None:
    """Ensure the ``ErrorResponse`` schema is present in the OpenAPI spec."""

    if hasattr(app, "_error_schema_registered"):
        return

    original_openapi = app.openapi

    def custom_openapi() -> dict:  # pragma: no cover - executed when generating docs
        if app.openapi_schema is not None:
            return app.openapi_schema
        schema = original_openapi()
        components = schema.setdefault("components", {}).setdefault("schemas", {})
        components.setdefault(
            "ErrorResponse",
            ErrorResponse.model_json_schema(ref_template="#/components/schemas/{model}"),
        )
        app.openapi_schema = schema
        return app.openapi_schema

    app.openapi = custom_openapi  # type: ignore[assignment]
    setattr(app, "_error_schema_registered", True)


__all__ = ["ErrorHandlingMiddleware"]
