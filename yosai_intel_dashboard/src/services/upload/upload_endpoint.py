"""Flask blueprint for handling file uploads.

The previous implementation relied on an asynchronous processor and returned a
job identifier to poll for status updates.  The blueprint now streams incoming
files directly to a configurable storage directory and immediately returns the
results of the upload.  Each file is validated using ``FileHandler.validator``
before it is written to disk.  Only whitelisted extensions and MIME types are
accepted and size limits are enforced prior to saving the file.
"""

from __future__ import annotations

import base64
from pathlib import Path

import redis
from flask import Blueprint, request
from flask_apispec import doc
from flask_wtf.csrf import validate_csrf
from pydantic import BaseModel, ConfigDict

from middleware.rate_limit import RedisRateLimiter, rate_limit
from yosai_intel_dashboard.src.error_handling import (
    ErrorCategory,
    ErrorHandler,
    api_error_response,
)
from yosai_intel_dashboard.src.infrastructure.config.loader import (
    ConfigurationLoader,
)
from yosai_intel_dashboard.src.services.data_processing.file_handler import FileHandler
from yosai_intel_dashboard.src.services.upload.file_validator import FileValidator
from yosai_intel_dashboard.src.utils.pydantic_decorators import (
    validate_input,
    validate_output,
)
from yosai_intel_dashboard.src.utils.sanitization import sanitize_filename

_service_cfg = ConfigurationLoader().get_service_config()
redis_client = redis.Redis.from_url(_service_cfg.redis_url)
rate_limiter = RedisRateLimiter(redis_client, {"default": {"limit": 100, "burst": 0}})


# ---------------------------------------------------------------------------
# Schema definitions
# ---------------------------------------------------------------------------


class UploadRequestSchema(BaseModel):
    """Payload schema for uploads.

    Files can either be supplied as base64 encoded strings in ``contents`` with
    matching ``filenames`` or via a traditional multipart form upload.
    """

    contents: list[str] | None = None
    filenames: list[str] | None = None

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "contents": ["data:text/plain;base64,SGVsbG8sIFdvcmxkIQ=="],
                    "filenames": ["hello.txt"],
                }
            ]
        }


class UploadResultSchema(BaseModel):
    """Details for a single uploaded file."""

    filename: str
    path: str


class UploadResponseSchema(BaseModel):
    """Response payload returned from the upload endpoint."""

    results: list[UploadResultSchema]

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "results": [
                        {
                            "filename": "hello.txt",
                            "path": "/tmp/uploads/hello.txt",
                        }
                    ]
                }
            ]
        }
    )


ALLOWED_MIME_TYPES: set[str] = {
    "text/csv",
    "application/json",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------


def stream_upload(storage_dir: Path, filename: str, data: bytes) -> Path:
    """Persist ``data`` to ``storage_dir`` using ``filename``.

    The directory is created if it does not yet exist.  The function returns the
    absolute path to the saved file.
    """

    storage_dir.mkdir(parents=True, exist_ok=True)
    dest = storage_dir / filename
    with open(dest, "wb") as f:
        f.write(data)
    return dest


def _decode_base64(content: str) -> tuple[str, bytes]:
    """Return MIME type and decoded bytes from a data URL string."""

    if "," not in content:
        raise ValueError("Invalid contents")
    header, data = content.split(",", 1)
    mime = header.split(";")[0].replace("data:", "", 1) or "application/octet-stream"
    return mime, base64.b64decode(data)


# ---------------------------------------------------------------------------
# Blueprint factory
# ---------------------------------------------------------------------------


def create_upload_blueprint(
    storage_dir: str | Path,
    *,
    file_handler: FileHandler | None = None,
    handler: ErrorHandler | None = None,
) -> Blueprint:
    """Return a blueprint handling file uploads.

    Parameters
    ----------
    storage_dir:
        Directory where uploaded files should be written.
    file_handler:
        Optional :class:`FileHandler` used to obtain the security validator.
    handler:
        Optional custom :class:`ErrorHandler`.
    """

    upload_bp = Blueprint("upload", __name__)
    err_handler = handler or ErrorHandler()
    storage_path = Path(storage_dir)

    validator = None
    if file_handler is not None:
        validator = getattr(file_handler, "validator", None)
    if validator is None:
        validator = FileHandler().validator

    file_validator = FileValidator(storage_path)

    @upload_bp.route("/v1/upload", methods=["POST"])
    @doc(
        description="Upload one or more files",
        tags=["upload"],
        responses={
            200: "Success",
            400: "Bad Request",
            401: "Unauthorized",
            500: "Internal Server Error",
        },
    )
    @validate_input(UploadRequestSchema)
    @validate_output(UploadResponseSchema)
    @rate_limit(rate_limiter)
    def upload_files(payload: UploadRequestSchema):
        """Validate and persist uploaded files."""

        try:
            token = (
                request.headers.get("X-CSRFToken")
                or request.headers.get("X-CSRF-Token")
                or request.form.get("csrf_token")
            )
            validate_csrf(token)
        except Exception:
            return api_error_response(
                ValueError("Invalid CSRF token"),
                ErrorCategory.INVALID_INPUT,
                handler=err_handler,
            )

        results: list[dict[str, str]] = []

        try:
            if request.files:
                for file in request.files.values():
                    if not file.filename:
                        continue
                    try:
                        filename = sanitize_filename(file.filename)
                    except ValueError as exc:
                        return api_error_response(
                            exc, ErrorCategory.INVALID_INPUT, handler=err_handler
                        )

                    mime = file.mimetype or "application/octet-stream"
                    if mime not in ALLOWED_MIME_TYPES:
                        return api_error_response(
                            ValueError("Unsupported file type"),
                            ErrorCategory.INVALID_INPUT,
                            handler=err_handler,
                        )

                    data = file.read()
                    try:
                        file_validator.validate(filename, mime, data)
                        res = validator.validate_file_upload(filename, data)
                        if not res.valid:
                            raise ValueError(", ".join(res.issues or []))
                    except Exception as exc:
                        return api_error_response(
                            exc, ErrorCategory.INVALID_INPUT, handler=err_handler
                        )
                    dest = stream_upload(storage_path, filename, data)
                    results.append({"filename": filename, "path": str(dest)})
            else:
                contents = payload.contents or []
                filenames = payload.filenames or []
                for content, name in zip(contents, filenames):
                    try:
                        filename = sanitize_filename(name)
                    except ValueError as exc:
                        return api_error_response(
                            exc, ErrorCategory.INVALID_INPUT, handler=err_handler
                        )

                    try:
                        mime, data = _decode_base64(content)
                    except Exception as exc:
                        return api_error_response(
                            exc, ErrorCategory.INVALID_INPUT, handler=err_handler
                        )

                    if mime not in ALLOWED_MIME_TYPES:
                        return api_error_response(
                            ValueError("Unsupported file type"),
                            ErrorCategory.INVALID_INPUT,
                            handler=err_handler,
                        )

                    try:
                        file_validator.validate(filename, mime, data)
                        res = validator.validate_file_upload(filename, data)
                        if not res.valid:
                            raise ValueError(", ".join(res.issues or []))
                    except Exception as exc:
                        return api_error_response(
                            exc, ErrorCategory.INVALID_INPUT, handler=err_handler
                        )

                    dest = stream_upload(storage_path, filename, data)
                    results.append({"filename": filename, "path": str(dest)})

        except Exception as exc:  # pragma: no cover - defensive
            return api_error_response(exc, ErrorCategory.INTERNAL, handler=err_handler)

        if not results:
            return api_error_response(
                ValueError("No file provided"),
                ErrorCategory.INVALID_INPUT,
                handler=err_handler,
            )

        return {"results": results}, 200

    return upload_bp


__all__ = [
    "UploadRequestSchema",
    "UploadResultSchema",
    "UploadResponseSchema",
    "create_upload_blueprint",
    "stream_upload",
    "ALLOWED_MIME_TYPES",
]
