from __future__ import annotations

import unicodedata
from typing import Any


def normalize_text(text: str) -> str:
    """Return ``text`` normalized to NFC with surrogate pairs handled.

    The input may contain explicit surrogate code points. Valid pairs are
    combined into their corresponding Unicode characters while unpaired
    surrogates are discarded.
    """
    if not isinstance(text, str):
        text = str(text)
    # Convert surrogate pairs and drop unpaired surrogates
    text = text.encode("utf-16", "surrogatepass").decode("utf-16", "ignore")
    return unicodedata.normalize("NFC", text)


def safe_decode_bytes(data: bytes, encoding: str = "utf-8") -> str:
    """Decode ``data`` using ``encoding`` while handling surrogate pairs."""
    try:
        text = data.decode(encoding, errors="surrogatepass")
    except Exception:
        text = data.decode(encoding, errors="ignore")
    return normalize_text(text)


def safe_encode_text(value: Any) -> str:
    """Return a normalized string representation of ``value``."""
    if isinstance(value, bytes):
        return safe_decode_bytes(value)
    return normalize_text(value)


__all__ = ["normalize_text", "safe_encode_text", "safe_decode_bytes"]
