# -*- coding: utf-8 -*-
import base64

from flask import Blueprint, jsonify, request
from flask_apispec import doc
from flask_wtf.csrf import validate_csrf
from pydantic import BaseModel

from services.upload.service_registration import register_upload_services

# Use the shared DI container configured at application startup
from core.container import container
from error_handling import ErrorCategory, ErrorHandler, api_error_response
from services.data_processing.file_handler import FileHandler
from utils.pydantic_decorators import validate_input, validate_output

if not container.has("upload_processor"):
    register_upload_services(container)

upload_bp = Blueprint("upload", __name__)

handler = ErrorHandler()


class UploadRequestSchema(BaseModel):
    contents: list[str] | None = None
    filenames: list[str] | None = None


class UploadResponseSchema(BaseModel):
    job_id: str


class StatusSchema(BaseModel):
    status: dict


@upload_bp.route("/v1/upload", methods=["POST"])
@doc(
    description="Upload a file",
    tags=["upload"],
    responses={202: "Accepted", 400: "Invalid CSRF token", 500: "Server Error"},
)
@validate_input(UploadRequestSchema)
@validate_output(UploadResponseSchema)
def upload_files(payload: UploadRequestSchema):
    """Handle file upload and return expected structure for React frontend"""
    try:
        token = (
            request.headers.get("X-CSRFToken")
            or request.headers.get("X-CSRF-Token")
            or request.form.get("csrf_token")
        )
        try:
            validate_csrf(token)
        except Exception:
            return api_error_response(
                ValueError("Invalid CSRF token"),
                ErrorCategory.INVALID_INPUT,
                handler=handler,
            )

        contents = []
        filenames = []
        file_processor = container.get("file_processor")
        validator = getattr(file_processor, "validator", None)
        if validator is None:
            try:
                validator = container.get("file_handler")
            except Exception:
                validator = FileHandler().validator

        # Support both multipart/form-data and raw JSON payloads
        if request.files:
            for file in request.files.values():
                if not file.filename:
                    continue
                file_bytes = file.read()
                try:
                    validator.validate_file_upload(file.filename, file_bytes)
                except Exception as exc:
                    return api_error_response(
                        exc,
                        ErrorCategory.INVALID_INPUT,
                        handler=handler,
                    )
                b64 = base64.b64encode(file_bytes).decode("utf-8", errors="replace")
                mime = file.mimetype or "application/octet-stream"
                contents.append(f"data:{mime};base64,{b64}")
                filenames.append(file.filename)
        else:
            contents = payload.contents or []
            filenames = payload.filenames or []

        if not contents or not filenames:
            return api_error_response(
                ValueError("No file provided"),
                ErrorCategory.INVALID_INPUT,
                handler=handler,
            )

        job_id = file_processor.process_file_async(contents[0], filenames[0])

        return {"job_id": job_id}, 202

    except Exception as e:
        return api_error_response(e, ErrorCategory.INTERNAL, handler=handler)


@upload_bp.route("/v1/upload/status/<job_id>", methods=["GET"])
@doc(
    params={
        "job_id": {
            "description": "Upload job id",
            "in": "path",
            "schema": {"type": "string"},
        }
    },
    tags=["upload"],
    responses={200: "Success"},
)
@validate_output(StatusSchema)
def upload_status(job_id: str):
    """Return background processing status for ``job_id``."""
    file_processor = container.get("file_processor")
    status = file_processor.get_job_status(job_id)
    return status
