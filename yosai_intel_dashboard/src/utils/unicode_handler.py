from __future__ import annotations

"""Unified Unicode sanitization wrapper."""

import logging
from typing import Any, Iterable, Mapping

from yosai_intel_dashboard.src.core.base_utils import (
    safe_encode_text as _safe_encode_text,
)

logger = logging.getLogger(__name__)


class UnicodeHandler:
    """Utility class for sanitizing arbitrary data."""

    @staticmethod
    def sanitize(obj: Any) -> Any:
        """Recursively sanitize ``obj`` for safe Unicode usage."""
        if isinstance(obj, (str, bytes, bytearray)):
            return _safe_encode_text(obj)
        if isinstance(obj, Mapping):
            return {k: UnicodeHandler.sanitize(v) for k, v in obj.items()}
        if isinstance(obj, Iterable) and not isinstance(obj, (bytes, bytearray)):
            return type(obj)(UnicodeHandler.sanitize(v) for v in obj)
        return obj

    @staticmethod
    def safe_encode_text(value: Any) -> str:
        """Expose underlying :func:`safe_encode_text` for convenience."""
        return _safe_encode_text(value)


safe_encode_text = UnicodeHandler.safe_encode_text


__all__ = ["UnicodeHandler", "safe_encode_text"]
