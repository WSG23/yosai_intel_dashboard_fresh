"""Lightweight Unicode helpers for analytics services."""

from __future__ import annotations

import unicodedata


def normalize_text(text: str) -> str:
    """Return ``text`` normalised using Unicode NFKC form.

    Parameters
    ----------
    text:
        Input text to normalise. Non-string values are converted to string and
        ``None`` becomes an empty string.
    """

    if text is None:
        return ""
    return unicodedata.normalize("NFKC", str(text))
