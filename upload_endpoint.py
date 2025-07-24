# -*- coding: utf-8 -*-
import base64

from flask import Blueprint, abort, jsonify, request
from flask_wtf.csrf import validate_csrf
from marshmallow import Schema, fields
from flask_apispec import doc, marshal_with, use_kwargs

from config.service_registration import register_upload_services

# Use the shared DI container configured at application startup
from core.container import container

if not container.has("upload_processor"):
    register_upload_services(container)

upload_bp = Blueprint("upload", __name__)


class UploadResponseSchema(Schema):
    job_id = fields.String()


class StatusSchema(Schema):
    status = fields.Dict()


@upload_bp.route("/v1/upload", methods=["POST"])
@doc(description="Upload a file", tags=["upload"])
@marshal_with(UploadResponseSchema, code=202)
def upload_files():
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
            abort(400, description="Invalid CSRF token")

        contents = []
        filenames = []

        # Support both multipart/form-data and raw JSON payloads
        if request.files:
            for file in request.files.values():
                if not file.filename:
                    continue
                file_bytes = file.read()
                b64 = base64.b64encode(file_bytes).decode('utf-8', errors='replace')
                mime = file.mimetype or "application/octet-stream"
                contents.append(f"data:{mime};base64,{b64}")
                filenames.append(file.filename)
        else:
            data = request.get_json(silent=True) or {}
            contents = data.get("contents", [])
            filenames = data.get("filenames", [])

        file_processor = container.get("file_processor")
        if not contents or not filenames:
            abort(400, description="No file provided")

        job_id = file_processor.process_file_async(contents[0], filenames[0])

        return jsonify({"job_id": job_id}), 202

    except Exception as e:
        abort(500, description=str(e))


@upload_bp.route("/v1/upload/status/<job_id>", methods=["GET"])
@doc(params={"job_id": "Upload job id"}, tags=["upload"])
@marshal_with(StatusSchema)
def upload_status(job_id: str):
    """Return background processing status for ``job_id``."""
    file_processor = container.get("file_processor")
    status = file_processor.get_job_status(job_id)
    return jsonify(status)
