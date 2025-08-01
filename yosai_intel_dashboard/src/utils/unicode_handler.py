from __future__ import annotations

"""Unified Unicode sanitization wrapper."""

import logging
from typing import Any, Iterable, Mapping

from yosai_intel_dashboard.src.core.unicode import sanitize_for_utf8

logger = logging.getLogger(__name__)


class UnicodeHandler:
    """Utility class for sanitizing arbitrary data."""

    @staticmethod
    def sanitize(obj: Any) -> Any:
        """Recursively sanitize ``obj`` for safe Unicode usage."""
        if isinstance(obj, str):
            return sanitize_for_utf8(obj)
        if isinstance(obj, Mapping):
            return {k: UnicodeHandler.sanitize(v) for k, v in obj.items()}
        if isinstance(obj, Iterable) and not isinstance(obj, (bytes, bytearray)):
            return type(obj)(UnicodeHandler.sanitize(v) for v in obj)
        return obj


__all__ = ["UnicodeHandler"]
