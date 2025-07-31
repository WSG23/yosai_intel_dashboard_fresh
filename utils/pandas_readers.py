"""Shared pandas file reader helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import json
import pandas as pd

from yosai_intel_dashboard.src.services.upload.utils.file_parser import UnicodeFileProcessor


def _sanitize(df: pd.DataFrame, processor: UnicodeFileProcessor | None) -> pd.DataFrame:
    proc = processor or UnicodeFileProcessor()
    return proc.sanitize_dataframe_unicode(df)


def read_csv(
    path: str | Path, *, processor: UnicodeFileProcessor | None = None, **kwargs: Any
) -> pd.DataFrame:
    """Read a CSV file and sanitize Unicode."""
    df = pd.read_csv(path, **kwargs)
    return _sanitize(df, processor)


def read_excel(
    path: str | Path, *, processor: UnicodeFileProcessor | None = None, **kwargs: Any
) -> pd.DataFrame:
    """Read an Excel file and sanitize Unicode."""
    df = pd.read_excel(path, **kwargs)
    return _sanitize(df, processor)


def read_json(
    path: str | Path,
    *,
    processor: UnicodeFileProcessor | None = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """Read a JSON file and sanitize Unicode."""
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    try:
        data = json.loads(text)
        df = pd.json_normalize(data)
    except json.JSONDecodeError:
        df = pd.read_json(text, lines=True)
    return _sanitize(df, processor)


def read_parquet(
    path: str | Path, *, processor: UnicodeFileProcessor | None = None, **kwargs: Any
) -> pd.DataFrame:
    """Read a parquet file and sanitize Unicode."""
    df = pd.read_parquet(path, **kwargs)
    return _sanitize(df, processor)


def read_fwf(
    path: str | Path, *, processor: UnicodeFileProcessor | None = None, **kwargs: Any
) -> pd.DataFrame:
    """Read a fixed-width file and sanitize Unicode."""
    df = pd.read_fwf(path, **kwargs)
    return _sanitize(df, processor)


__all__ = ["read_csv", "read_excel", "read_json", "read_parquet", "read_fwf"]
