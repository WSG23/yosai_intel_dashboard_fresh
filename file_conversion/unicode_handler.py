"""Utilities for cleaning Unicode surrogate characters."""

from __future__ import annotations

import logging
import pandas as pd
from pandas import DataFrame

from plugins.service_locator import PluginServiceLocator

_logger = logging.getLogger(__name__)

_unicode = PluginServiceLocator.get_unicode_handler()
UnicodeProcessor = _unicode.UnicodeProcessor


class UnicodeCleaner:
    """Helper class to remove invalid Unicode surrogate characters."""

    @staticmethod
    def clean_string(text: str) -> str:
        """Return ``text`` with surrogate characters removed."""
        try:
            return UnicodeProcessor.clean_surrogate_chars(text)
        except Exception as exc:  # pragma: no cover - best effort
            _logger.error("Error cleaning string: %s", exc)
            return text

    @staticmethod
    def clean_dataframe(df: DataFrame) -> DataFrame:
        """Return a copy of ``df`` with surrogate characters removed."""
        try:
            return UnicodeProcessor.sanitize_dataframe(df)
        except Exception as exc:  # pragma: no cover - best effort
            _logger.error("Error cleaning DataFrame: %s", exc)
            return df


__all__ = ["UnicodeCleaner"]
