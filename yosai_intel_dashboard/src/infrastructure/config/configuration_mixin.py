"""Shared configuration helpers."""

from __future__ import annotations


class ConfigurationMixin:
    """Mixin providing helper accessors for common configuration values."""

    AI_CONFIDENCE_DEFAULT: float = 0.8
    MAX_UPLOAD_SIZE_DEFAULT: int = 50
    UPLOAD_CHUNK_SIZE_DEFAULT: int = 1024

    def get_ai_confidence_threshold(self) -> float:
        perf = getattr(self, "performance", None)
        if perf and hasattr(perf, "ai_confidence_threshold"):
            return float(perf.ai_confidence_threshold)
        return float(
            getattr(self, "ai_confidence_threshold", self.AI_CONFIDENCE_DEFAULT)
        )

    def get_max_upload_size_mb(self) -> int:
        security = getattr(self, "security", None)
        if security and hasattr(security, "max_upload_mb"):
            return int(security.max_upload_mb)
        upload = getattr(self, "upload", None)
        if upload and hasattr(upload, "max_file_size_mb"):
            return int(upload.max_file_size_mb)
        return int(
            getattr(self, "max_upload_size_mb", self.MAX_UPLOAD_SIZE_DEFAULT)
        )

    def get_upload_chunk_size(self) -> int:
        uploads = getattr(self, "uploads", None)
        if uploads and hasattr(uploads, "DEFAULT_CHUNK_SIZE"):
            return int(uploads.DEFAULT_CHUNK_SIZE)
        return int(
            getattr(self, "upload_chunk_size", self.UPLOAD_CHUNK_SIZE_DEFAULT)
        )


__all__ = ["ConfigurationMixin"]
