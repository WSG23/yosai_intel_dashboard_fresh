"""Minimal Unicode utilities for tests."""
import logging
import re
import unicodedata
from typing import Any

logger = logging.getLogger(__name__)
_SURROGATE_RE = re.compile(r"[\uD800-\uDFFF]")
_CONTROL_RE = re.compile(r"[\x00-\x1F\x7F]")


def sanitize_unicode_input(text: Any, replacement: str = "\uFFFD") -> str:
    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:
            logger.warning("Failed to convert %r to str", text, exc_info=True)
            return ""
    try:
        cleaned = _SURROGATE_RE.sub(replacement, text)
        cleaned = unicodedata.normalize("NFKC", cleaned)
        cleaned = _CONTROL_RE.sub("", cleaned)
        cleaned.encode("utf-8")
        return cleaned
    except Exception as exc:
        logger.error("sanitize_unicode_input failed: %s", exc)
        return "".join(ch for ch in str(text) if ch.isascii())


__all__ = ["sanitize_unicode_input"]
