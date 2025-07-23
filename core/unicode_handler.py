from __future__ import annotations

"""Shared Unicode handling utilities."""

import re
from typing import Any


_SURROGATE_RE = re.compile(r"[\uD800-\uDFFF]")


def clean_unicode_surrogates(text: Any) -> str:
    """Return ``text`` with Unicode surrogate characters removed."""

    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:
            return ""

    return _SURROGATE_RE.sub("", text)


__all__ = ["clean_unicode_surrogates"]
