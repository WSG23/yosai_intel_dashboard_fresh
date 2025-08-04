from __future__ import annotations

"""Mixin providing access to common configuration values."""

from typing import Any, Mapping


class ConfigurationMixin:
    """Provide standard getters for configuration values.

    The mixin looks for values across several possible attribute names and
    locations to maintain compatibility with different configuration objects.
    The public methods accept an optional ``cfg`` argument allowing them to be
    used both as mixin methods and as stand‑alone helpers operating on arbitrary
    configuration objects or mappings.
    """

    @staticmethod
    def _get_attr(obj: Any, names: tuple[str, ...]) -> Any | None:
        """Retrieve an attribute or mapping key from ``obj``."""

        if obj is None:
            return None
        if isinstance(obj, Mapping):
            for name in names:
                if name in obj:
                    return obj[name]
            return None
        for name in names:
            if hasattr(obj, name):
                return getattr(obj, name)
        return None

    # AI confidence threshold -------------------------------------------------
    def get_ai_confidence_threshold(self, cfg: Any | None = None) -> float:
        """Return the AI confidence threshold with fallbacks."""

        obj = self if cfg is None else cfg
        perf = getattr(obj, "performance", None)
        if perf is not None:
            value = ConfigurationMixin._get_attr(
                perf, ("ai_confidence_threshold", "ai_threshold")
            )
            if value is not None:
                return float(value)
        value = ConfigurationMixin._get_attr(
            obj, ("ai_confidence_threshold", "ai_threshold")
        )
        if value is not None:
            return float(value)
        return 0.8

    # Maximum upload size -----------------------------------------------------
    def get_max_upload_size_mb(self, cfg: Any | None = None) -> int:
        """Return maximum upload size in megabytes with fallbacks."""

        obj = self if cfg is None else cfg
        value = ConfigurationMixin._get_attr(
            obj, ("max_upload_size_mb", "max_upload_mb", "max_size_mb")
        )
        if value is not None:
            return int(value)
        sec = getattr(obj, "security", None)
        if sec is not None:
            value = ConfigurationMixin._get_attr(
                sec, ("max_upload_mb", "max_upload_size_mb", "max_size_mb")
            )
            if value is not None:
                return int(value)
        upload = getattr(obj, "upload", None)
        if upload is not None:
            value = ConfigurationMixin._get_attr(upload, ("max_file_size_mb",))
            if value is not None:
                return int(value)
        return 50

    # Upload chunk size -------------------------------------------------------
    def get_upload_chunk_size(self, cfg: Any | None = None) -> int:
        """Return default upload chunk size with fallbacks."""

        obj = self if cfg is None else cfg
        value = ConfigurationMixin._get_attr(obj, ("upload_chunk_size", "chunk_size"))
        if value is not None:
            return int(value)
        uploads = getattr(obj, "uploads", None)
        if uploads is not None:
            value = ConfigurationMixin._get_attr(
                uploads, ("DEFAULT_CHUNK_SIZE", "chunk_size", "upload_chunk_size")
            )
            if value is not None:
                return int(value)
        return 1024



__all__ = ["ConfigurationMixin"]
