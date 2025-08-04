from __future__ import annotations

"""Mixin providing access to common configuration values."""

from typing import Any


class ConfigurationMixin:
    """Provide standard getters for configuration values.

    The mixin looks for values across several possible attribute names and
    locations to maintain compatibility with different configuration objects.
    """

    def _get_attr(self, obj: Any, names: tuple[str, ...]) -> Any | None:
        for name in names:
            if hasattr(obj, name):
                return getattr(obj, name)
        return None

    # AI confidence threshold -------------------------------------------------
    def get_ai_confidence_threshold(self) -> float:
        """Return the AI confidence threshold with fallbacks."""
        # Check nested performance object
        perf = getattr(self, "performance", None)
        if perf is not None:
            value = self._get_attr(perf, ("ai_confidence_threshold", "ai_threshold"))
            if value is not None:
                return float(value)
        # Direct attributes
        value = self._get_attr(self, ("ai_confidence_threshold", "ai_threshold"))
        if value is not None:
            return float(value)
        return 0.8

    # Maximum upload size -----------------------------------------------------
    def get_max_upload_size_mb(self) -> int:
        """Return maximum upload size in megabytes with fallbacks."""
        sec = getattr(self, "security", None)
        if sec is not None:
            value = self._get_attr(
                sec,
                ("max_upload_mb", "max_upload_size_mb", "max_size_mb"),
            )
            if value is not None:
                return int(value)
        # Root level attributes
        value = self._get_attr(
            self, ("max_upload_size_mb", "max_upload_mb", "max_size_mb")
        )
        if value is not None:
            return int(value)
        # Upload sub-object
        upload = getattr(self, "upload", None)
        if upload is not None:
            value = self._get_attr(upload, ("max_file_size_mb",))
            if value is not None:
                return int(value)
        return 50

    # Upload chunk size -------------------------------------------------------
    def get_upload_chunk_size(self) -> int:
        """Return default upload chunk size with fallbacks."""
        uploads = getattr(self, "uploads", None)
        if uploads is not None:
            value = self._get_attr(
                uploads, ("DEFAULT_CHUNK_SIZE", "chunk_size", "upload_chunk_size")
            )
            if value is not None:
                return int(value)
        value = self._get_attr(self, ("upload_chunk_size", "chunk_size"))
        if value is not None:
            return int(value)
        return 1024


__all__ = ["ConfigurationMixin"]
