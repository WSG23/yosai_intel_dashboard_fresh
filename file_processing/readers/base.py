from __future__ import annotations

from typing import Dict, Optional

import pandas as pd

from core.unicode_processor import UnicodeProcessor


class BaseReader:
    """Base class for file readers."""

    format_name: str = "base"

    class CannotParse(Exception):
        """Raised when a reader cannot parse a file."""

    def read(self, file_path: str, hint: Optional[Dict] = None) -> pd.DataFrame:
        raise NotImplementedError

    @staticmethod
    def _sanitize(df: pd.DataFrame) -> pd.DataFrame:
        return UnicodeProcessor.sanitize_dataframe(df)

