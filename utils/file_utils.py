from __future__ import annotations

"""Helper utilities for working with files."""

from core.unicode_utils import sanitize_for_utf8
from core.unicode_decode import safe_unicode_decode


def safe_decode_with_unicode_handling(data: bytes, encoding: str) -> str:
    """Decode bytes using ``encoding`` and sanitize output."""
    text = safe_unicode_decode(data, encoding)
    cleaned = sanitize_for_utf8(text)
    return cleaned.replace("\ufffd", "")


__all__ = ["safe_decode_with_unicode_handling"]
