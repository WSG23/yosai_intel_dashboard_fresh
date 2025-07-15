from typing import Any

import pandas as pd

from core.unicode import sanitize_unicode_input, clean_surrogate_chars


class UnicodeProcessor:
    """Handle Unicode surrogate characters safely."""

    @staticmethod
    def clean_unicode_surrogates(text: str) -> str:
        return clean_surrogate_chars(text)

    @staticmethod
    def safe_encode_utf8(text: str) -> bytes:
        return sanitize_unicode_input(text).encode("utf-8", errors="ignore")

    @staticmethod
    def process_dataframe_unicode(df: pd.DataFrame) -> pd.DataFrame:
        return df.applymap(lambda x: clean_surrogate_chars(str(x)) if isinstance(x, str) else x)
