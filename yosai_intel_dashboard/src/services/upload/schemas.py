from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel


class UploadResult(BaseModel):
    """Status information for an upload job.

    The ``status`` field may contain arbitrary metadata describing the current
    state of the upload process.
    """

    status: Dict[str, Any]

    class Config:
        json_schema_extra = {"examples": [{"status": {"state": "processing"}}]}


class UploadResponse(BaseModel):
    """Response returned when an upload job is accepted."""

    job_id: str

    class Config:
        json_schema_extra = {
            "examples": [
                {"job_id": "123e4567-e89b-12d3-a456-426614174000"}
            ]
        }


__all__ = ["UploadResult", "UploadResponse"]
