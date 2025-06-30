#!/usr/bin/env python3
"""Unicode processing helpers with surrogate cleanup and large CSV handling."""

from __future__ import annotations

import logging
import re
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def safe_unicode_encode(value: Any) -> str:
    """Return a valid UTF-8 string removing invalid surrogates."""
    if isinstance(value, bytes):
        try:
            value = value.decode("utf-8", "surrogatepass")
        except Exception:
            value = value.decode("latin-1", "surrogatepass")
    else:
        value = str(value)

    value = re.sub(r"[\ud800-\udfff]", "", value)
    return value.encode("utf-8", "ignore").decode("utf-8", "ignore")


def clean_unicode_surrogates(text: Any) -> str:
    """Remove Unicode surrogate characters from text."""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return ""
    text = str(text)
    text = re.sub(r"[\ud800-\udfff]", "", text)
    text = text.replace("\ufffe", "").replace("\uffff", "")
    return text


def sanitize_data_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitize DataFrame column names and string values."""
    df_clean = df.copy()

    new_columns = []
    for col in df_clean.columns:
        safe_col = clean_unicode_surrogates(col)
        safe_col = re.sub(r"^[=+\-@]+", "", safe_col)
        new_columns.append(safe_col)
    df_clean.columns = new_columns

    for col in df_clean.select_dtypes(include=["object"]).columns:
        df_clean[col] = df_clean[col].map(clean_unicode_surrogates)

    return df_clean


def sanitize_unicode_input(value: Any) -> str:
    """Sanitize a single input value containing possible surrogates."""
    return clean_unicode_surrogates(value)


def process_large_csv_content(content: bytes, encoding: str = "utf-8", *, chunk_size: int = 1024 * 1024) -> str:
    """Decode potentially large CSV content in chunks and sanitize."""
    pieces: list[str] = []
    mv = memoryview(content)
    for start in range(0, len(mv), chunk_size):
        chunk = mv[start : start + chunk_size].tobytes()
        text = chunk.decode(encoding, errors="surrogatepass")
        pieces.append(clean_unicode_surrogates(text))
    return "".join(pieces)

__all__ = [
    "safe_unicode_encode",
    "sanitize_data_frame",
    "clean_unicode_surrogates",
    "sanitize_unicode_input",
    "process_large_csv_content",
]
