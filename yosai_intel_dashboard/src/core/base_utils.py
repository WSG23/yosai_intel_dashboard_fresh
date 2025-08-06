"""Lightweight text processing helpers used across the project.

These utilities provide safe Unicode handling without importing any other
project modules.  They intentionally offer a small subset of the features from
:mod:`core.unicode` so that they can be imported in low level modules without
creating circular dependencies.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

# Precompiled regular expressions for performance
_CONTROL_RE = re.compile(r"[\x00-\x1F\x7F]")
_SURROGATE_RE = re.compile(r"[\uD800-\uDFFF]")
_DANGEROUS_PREFIX_RE = re.compile(r"^[=+\-@]+")


def clean_surrogate_chars(text: str, replacement: str = "") -> str:
    """Return ``text`` with surrogate code points removed or replaced."""

    out: list[str] = []
    i = 0
    while i < len(text):
        ch = text[i]
        code = ord(ch)
        # High surrogate
        if 0xD800 <= code <= 0xDBFF:
            if i + 1 < len(text):
                next_code = ord(text[i + 1])
                if 0xDC00 <= next_code <= 0xDFFF:
                    pair = ((code - 0xD800) << 10) + (next_code - 0xDC00) + 0x10000
                    out.append(chr(pair))
                    i += 2
                    continue
            if replacement:
                out.append(replacement)
            i += 1
            continue
        # Low surrogate without preceding high surrogate
        if 0xDC00 <= code <= 0xDFFF:
            if replacement:
                out.append(replacement)
            i += 1
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def clean_unicode_text(text: Any) -> str:
    """Clean ``text`` of surrogates, control chars and dangerous prefixes."""

    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    text = clean_surrogate_chars(text)
    try:
        text = unicodedata.normalize("NFKC", text)
    except Exception:
        pass
    text = _SURROGATE_RE.sub("", text)
    text = _CONTROL_RE.sub("", text)
    text = _DANGEROUS_PREFIX_RE.sub("", text)
    try:
        text.encode("utf-8")
    except UnicodeEncodeError:
        text = text.encode("utf-8", "ignore").decode("utf-8", "ignore")
    return text


def safe_encode_text(value: Any) -> str:
    """Return ``value`` encoded safely as Unicode text."""

    if isinstance(value, bytes):
        try:
            value = value.decode("utf-8", errors="surrogatepass")
        except Exception:
            value = value.decode("utf-8", errors="ignore")
    return clean_unicode_text(value)


__all__ = [
    "safe_encode_text",
    "clean_surrogate_chars",
    "clean_unicode_text",
]
