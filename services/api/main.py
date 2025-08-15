from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from shared.errors import CODE_TO_STATUS, ErrorCode, ErrorResponse
try:  # Python 3.11+
    from builtins import ExceptionGroup  # type: ignore[attr-defined]
except Exception:  # pragma: no cover
    ExceptionGroup = None  # type: ignore[misc]

from services.api.middleware.body_size_limit import BodySizeLimitMiddleware
from services.api.middleware.security_headers import SecurityHeadersMiddleware

app = FastAPI()
app.add_middleware(BodySizeLimitMiddleware, max_bytes=50 * 1024 * 1024)
app.add_middleware(SecurityHeadersMiddleware)


def _build_error_response(
    code: ErrorCode, message: str, details: object | None = None, status_code: int | None = None
) -> JSONResponse:
    """Serialize an :class:`ErrorResponse` into a ``JSONResponse``."""

    payload = ErrorResponse(code=code, message=message, details=details)
    return JSONResponse(
        payload.model_dump(),
        status_code=status_code or CODE_TO_STATUS.get(code, 500),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:  # pragma: no cover - exercised via tests
    return _build_error_response(
        ErrorCode.INVALID_INPUT, "Invalid input", details=exc.errors(), status_code=400
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code = {
        400: ErrorCode.INVALID_INPUT,
        401: ErrorCode.UNAUTHORIZED,
        404: ErrorCode.NOT_FOUND,
    }.get(exc.status_code, ErrorCode.INTERNAL)
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return _build_error_response(code, message, status_code=exc.status_code)


# Ensure 404 errors raised by the router also go through ``http_exception_handler``
app.add_exception_handler(404, http_exception_handler)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return _build_error_response(ErrorCode.INTERNAL, "Internal Server Error", status_code=500)


if ExceptionGroup is not None:
    @app.exception_handler(ExceptionGroup)  # type: ignore[arg-type]
    async def exception_group_handler(request: Request, exc: ExceptionGroup) -> JSONResponse:
        return _build_error_response(ErrorCode.INTERNAL, "Internal Server Error", status_code=500)


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
