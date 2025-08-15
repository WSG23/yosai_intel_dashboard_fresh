from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from shared.errors import ErrorCode, fastapi_error_response
from shared.errors.helpers import ServiceError

try:  # Python 3.11+
    from builtins import ExceptionGroup
except Exception:  # pragma: no cover
    ExceptionGroup = Exception  # type: ignore[misc, assignment]

from services.api.middleware.body_size_limit import BodySizeLimitMiddleware
from services.api.middleware.security_headers import SecurityHeadersMiddleware
from yosai_intel_dashboard.src.services.security import requires_role

app = FastAPI()
app.add_middleware(BodySizeLimitMiddleware, max_bytes=50 * 1024 * 1024)
app.add_middleware(SecurityHeadersMiddleware)


@app.exception_handler(RequestValidationError)  # type: ignore[misc]
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:  # pragma: no cover - exercised via tests
    err = ServiceError(ErrorCode.INVALID_INPUT, "Invalid input", exc.errors())
    return fastapi_error_response(err, status_code=400)


@app.exception_handler(HTTPException)  # type: ignore[misc]
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code = {
        400: ErrorCode.INVALID_INPUT,
        401: ErrorCode.UNAUTHORIZED,
        404: ErrorCode.NOT_FOUND,
    }.get(exc.status_code, ErrorCode.INTERNAL)
    message = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return fastapi_error_response(
        ServiceError(code, message), status_code=exc.status_code
    )


# Ensure 404 errors raised by the router also go through ``http_exception_handler``
app.add_exception_handler(404, http_exception_handler)


@app.exception_handler(Exception)  # type: ignore[misc]
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    err = ServiceError(ErrorCode.INTERNAL, "Internal Server Error")
    return fastapi_error_response(err, status_code=500)


if ExceptionGroup is not None:

    @app.exception_handler(ExceptionGroup)  # type: ignore[misc]
    async def exception_group_handler(
        request: Request, exc: ExceptionGroup[Exception]
    ) -> JSONResponse:
        err = ServiceError(ErrorCode.INTERNAL, "Internal Server Error")
        return fastapi_error_response(err, status_code=500)


@app.route("/health")  # type: ignore[misc]
async def health(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


class EchoRequest(BaseModel):  # type: ignore[misc]
    message: str


class EchoResponse(BaseModel):  # type: ignore[misc]
    message: str


@app.post("/api/v1/echo", response_model=EchoResponse)  # type: ignore[misc]
async def echo(
    body: EchoRequest, _: None = Depends(requires_role("admin"))
) -> EchoResponse:
    return EchoResponse(message=body.message)
