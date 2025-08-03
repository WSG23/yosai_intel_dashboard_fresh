"""Shared pandas file reader helpers."""

from __future__ import annotations

import json
import mmap
from pathlib import Path
from typing import Any

import pandas as pd

from yosai_intel_dashboard.src.file_processing import sanitize_dataframe_unicode


def _sanitize(df: pd.DataFrame, processor: Any | None) -> pd.DataFrame:
    if processor is not None and hasattr(processor, "sanitize_dataframe_unicode"):
        return processor.sanitize_dataframe_unicode(df)
    return sanitize_dataframe_unicode(df)


def read_csv(
    path: str | Path, *, processor: Any | None = None, **kwargs: Any
) -> pd.DataFrame:
    """Read a CSV file and sanitize Unicode."""
    kwargs.setdefault("memory_map", True)
    df = pd.read_csv(path, **kwargs)
    return _sanitize(df, processor)


def read_excel(
    path: str | Path, *, processor: Any | None = None, **kwargs: Any
) -> pd.DataFrame:
    """Read an Excel file and sanitize Unicode."""
    df = pd.read_excel(path, **kwargs)
    return _sanitize(df, processor)


def read_json(
    path: str | Path,
    *,
    processor: Any | None = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """Read a JSON file and sanitize Unicode."""
    with open(path, "rb") as fh:
        with mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            try:
                data = json.loads(mm)
                df = pd.json_normalize(data)
            except json.JSONDecodeError:
                mm.seek(0)
                df = pd.read_json(mm, lines=True, **kwargs)
    return _sanitize(df, processor)


def read_parquet(
    path: str | Path, *, processor: Any | None = None, **kwargs: Any
) -> pd.DataFrame:
    """Read a parquet file and sanitize Unicode."""
    df = pd.read_parquet(path, **kwargs)
    return _sanitize(df, processor)


def read_fwf(
    path: str | Path, *, processor: Any | None = None, **kwargs: Any
) -> pd.DataFrame:
    """Read a fixed-width file and sanitize Unicode."""
    df = pd.read_fwf(path, **kwargs)
    return _sanitize(df, processor)


__all__ = ["read_csv", "read_excel", "read_json", "read_parquet", "read_fwf"]
