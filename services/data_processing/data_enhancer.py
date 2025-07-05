from __future__ import annotations

"""Data enhancement helpers wrapping :class:`UnicodeProcessor`."""

from typing import Any

import pandas as pd
from plugins.service_locator import PluginServiceLocator

_unicode = PluginServiceLocator.get_unicode_handler()
UnicodeProcessor = _unicode.UnicodeProcessor


def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitize DataFrame using :class:`UnicodeProcessor`."""
    return UnicodeProcessor.sanitize_dataframe(df)


def clean_unicode_text(text: str) -> str:
    """Clean text by removing surrogate characters."""
    return UnicodeProcessor.clean_surrogate_chars(text)


__all__ = ["UnicodeProcessor", "sanitize_dataframe", "clean_unicode_text"]
