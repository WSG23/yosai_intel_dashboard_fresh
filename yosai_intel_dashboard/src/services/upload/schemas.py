from __future__ import annotations

from pydantic import BaseModel


class UploadResult(BaseModel):
    """Details for a single uploaded file."""

    filename: str
    path: str

    class Config:
        json_schema_extra = {
            "examples": [
                {"filename": "hello.txt", "path": "/tmp/uploads/hello.txt"}
            ]
        }


class UploadResponse(BaseModel):
    """Response payload returned from the upload endpoint."""

    results: list[UploadResult]

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "results": [
                        {"filename": "hello.txt", "path": "/tmp/uploads/hello.txt"}
                    ]
                }
            ]
        }


__all__ = ["UploadResult", "UploadResponse"]
