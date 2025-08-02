"""Backward-compatible exports for upload endpoint services."""

from __future__ import annotations

# Explicitly import only the public symbols from the upload endpoint module.
from .upload.upload_endpoint import (
    StatusSchema,
    UploadRequestSchema,
    UploadResponseSchema,
    create_upload_blueprint,
)

# Re-export the imported symbols to maintain the public API of this module.
__all__ = [
    "UploadRequestSchema",
    "UploadResponseSchema",
    "StatusSchema",
    "create_upload_blueprint",
]
