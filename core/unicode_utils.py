"""Unicode utilities used across the core security modules."""

from __future__ import annotations

import logging
import re
import unicodedata
from typing import Any

logger = logging.getLogger(__name__)

# Regular expressions for surrogate and control characters
_SURROGATE_RE = re.compile(r"[\uD800-\uDFFF]")
# Exclude common whitespace (tab/newline/carriage return)
_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def sanitize_unicode_input(text: Any, replacement: str = "\uFFFD") -> str:
    """Return ``text`` with surrogate and control characters removed.

    Parameters
    ----------
    text:
        Input that will be coerced to ``str``.
    replacement:
        Character used to replace surrogate code points.
    """

    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:  # pragma: no cover - defensive
            logger.warning("Failed to convert %r to str", text, exc_info=True)
            return ""

    try:
        cleaned = _SURROGATE_RE.sub(replacement, text)
        cleaned = _CONTROL_RE.sub("", cleaned)
        cleaned = unicodedata.normalize("NFKC", cleaned)
        cleaned.encode("utf-8")
        return cleaned
    except Exception as exc:  # pragma: no cover - best effort
        logger.error("sanitize_unicode_input failed: %s", exc)
        return "".join(ch for ch in str(text) if ch.isascii())


__all__ = ["sanitize_unicode_input"]
