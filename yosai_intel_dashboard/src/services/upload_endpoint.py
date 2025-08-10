"""Backward-compatible exports for upload endpoint services."""

from __future__ import annotations

import warnings

# Explicitly import only the public symbols from the upload endpoint module.
from .upload.upload_endpoint import (
    ALLOWED_MIME_TYPES,
    UploadRequestSchema,
    UploadResponseSchema,
    UploadResultSchema,
    create_upload_blueprint as _create_upload_blueprint,
    stream_upload,
)

# Re-export the imported symbols to maintain the public API of this module.
__all__ = [
    "UploadRequestSchema",
    "UploadResponseSchema",
    "UploadResultSchema",
    "create_upload_blueprint",
    "stream_upload",
    "ALLOWED_MIME_TYPES",
]


def create_upload_blueprint(*args, **kwargs):
    """Deprecated wrapper for :func:`upload.upload_endpoint.create_upload_blueprint`."""

    warnings.warn(
        "services.upload_endpoint.create_upload_blueprint is deprecated; "
        "use services.upload.upload_endpoint.create_upload_blueprint",
        DeprecationWarning,
        stacklevel=2,
    )
    return _create_upload_blueprint(*args, **kwargs)
