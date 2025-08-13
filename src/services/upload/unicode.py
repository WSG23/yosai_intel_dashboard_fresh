"""Unicode helpers for upload services leveraging :class:`UnicodeHandler`."""

from __future__ import annotations

from typing import Any

from unicode_toolkit import UnicodeHandler, safe_encode_text as _safe_encode_text


def normalize_text(text: Any) -> str:
    """Return normalized ``text`` using the shared encoder."""
    return _safe_encode_text(text)


def safe_decode_bytes(data: bytes, encoding: str = "utf-8") -> str:
    """Decode ``data`` with ``encoding`` and normalize the result."""
    try:
        text = data.decode(encoding, errors="surrogatepass")
    except Exception:
        text = data.decode(encoding, errors="ignore")
    return _safe_encode_text(text)


def safe_encode_text(value: Any) -> str:
    """Public wrapper around :func:`safe_encode_text`."""
    return _safe_encode_text(value)


__all__ = ["normalize_text", "safe_encode_text", "safe_decode_bytes"]
