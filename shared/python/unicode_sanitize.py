from __future__ import annotations

import re

_SURROGATES = re.compile(r"[\uD800-\uDFFF]")


def clean_surrogates(s: str) -> str:
    """
    Replace isolated surrogate code points with U+FFFD.
    Safe for logging, JSON, CSV, and HTML contexts.
    """
    return _SURROGATES.sub("\uFFFD", s)
