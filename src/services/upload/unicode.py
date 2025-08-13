"""Unicode helpers for upload services leveraging :class:`UnicodeHandler`."""

from __future__ import annotations

from typing import Any

from unicode_toolkit.helpers import UnicodeHandler


def normalize_text(text: Any) -> str:
    """Return sanitized and normalized ``text``."""
    return UnicodeHandler.sanitize(text)


def safe_decode_bytes(data: bytes, encoding: str = "utf-8") -> str:
    """Decode ``data`` with ``encoding`` and sanitize the result."""
    try:
        text = data.decode(encoding, errors="surrogatepass")
    except Exception:
        text = data.decode(encoding, errors="ignore")
    return UnicodeHandler.sanitize(text)


def safe_encode_text(value: Any) -> str:
    """Return a sanitized string representation of ``value``."""
    if isinstance(value, bytes):
        return safe_decode_bytes(value)
    return UnicodeHandler.sanitize(value)


__all__ = ["normalize_text", "safe_encode_text", "safe_decode_bytes"]
