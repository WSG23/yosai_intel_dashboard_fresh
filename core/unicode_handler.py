from __future__ import annotations

"""Deprecated Unicode helpers maintained for backward compatibility."""

from typing import Any
import warnings

from .unicode import clean_surrogate_chars


def clean_unicode_surrogates(text: Any) -> str:
    """Return ``text`` with surrogate characters removed."""

    warnings.warn(
        "core.unicode_handler.clean_unicode_surrogates is deprecated; "
        "use core.unicode.clean_surrogate_chars",
        DeprecationWarning,
        stacklevel=2,
    )

    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:
            return ""

    return clean_surrogate_chars(text)


__all__ = ["clean_unicode_surrogates"]
