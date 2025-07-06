from __future__ import annotations

"""Lightweight Unicode decoding helpers."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _remove_invalid_surrogates(text: str) -> str:
    """Return ``text`` without lone surrogate code points."""
    out = []
    i = 0
    while i < len(text):
        ch = text[i]
        code = ord(ch)
        if 0xD800 <= code <= 0xDBFF:
            if i + 1 < len(text) and 0xDC00 <= ord(text[i + 1]) <= 0xDFFF:
                out.append(ch)
                out.append(text[i + 1])
                i += 2
                continue
            i += 1
            continue
        if 0xDC00 <= code <= 0xDFFF:
            i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def safe_unicode_decode(data: Any, encoding: str = "utf-8") -> str:
    """Decode ``data`` safely removing invalid surrogates."""
    if isinstance(data, str):
        return _remove_invalid_surrogates(data)

    try:
        text = data.decode(encoding, errors="surrogatepass")
    except UnicodeError as exc:
        logger.warning("Primary decode failed: %s", exc)
        try:
            text = data.decode(encoding, errors="replace")
        except Exception:
            text = data.decode("utf-8", errors="ignore")
    return _remove_invalid_surrogates(text)


__all__ = ["safe_unicode_decode"]
