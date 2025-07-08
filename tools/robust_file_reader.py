from __future__ import annotations

"""Utility helpers for reading text files with encoding detection."""

from pathlib import Path
from typing import Iterable, Optional

try:
    import chardet
except Exception:  # pragma: no cover - optional dependency
    chardet = None  # type: ignore

from core.unicode_decode import safe_unicode_decode


def _detect_encoding(data: bytes) -> Optional[str]:
    """Return best-guess encoding for ``data`` using ``chardet`` if available."""
    if chardet is None:
        return None
    try:
        result = chardet.detect(data)
        return result.get("encoding")
    except Exception:  # pragma: no cover - defensive
        return None


def safe_read_text(path: Path, *, fallback_encodings: Optional[Iterable[str]] = None) -> str:
    """Return text from ``path`` using encoding detection and fallbacks."""
    data = path.read_bytes()
    encodings = []

    detected = _detect_encoding(data)
    if detected:
        encodings.append(detected)

    if fallback_encodings:
        encodings.extend(fallback_encodings)

    if "utf-8" not in encodings:
        encodings.append("utf-8")

    for encoding in encodings:
        try:
            return safe_unicode_decode(data, encoding)
        except Exception:
            continue

    return safe_unicode_decode(data, "utf-8")


__all__ = ["safe_read_text"]
