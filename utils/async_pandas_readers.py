from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pandas as pd

from services.upload.utils.file_parser import UnicodeFileProcessor

from .pandas_readers import (
    read_csv,
    read_excel,
    read_fwf,
    read_json,
    read_parquet,
)


async def async_read_csv(
    path: str | Path,
    *,
    processor: UnicodeFileProcessor | None = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """Asynchronously read a CSV file and sanitize Unicode."""
    return await asyncio.to_thread(read_csv, path, processor=processor, **kwargs)


async def async_read_excel(
    path: str | Path,
    *,
    processor: UnicodeFileProcessor | None = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """Asynchronously read an Excel file and sanitize Unicode."""
    return await asyncio.to_thread(read_excel, path, processor=processor, **kwargs)


async def async_read_json(
    path: str | Path,
    *,
    processor: UnicodeFileProcessor | None = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """Asynchronously read a JSON file and sanitize Unicode."""
    return await asyncio.to_thread(read_json, path, processor=processor, **kwargs)


async def async_read_parquet(
    path: str | Path,
    *,
    processor: UnicodeFileProcessor | None = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """Asynchronously read a Parquet file and sanitize Unicode."""
    return await asyncio.to_thread(read_parquet, path, processor=processor, **kwargs)


async def async_read_fwf(
    path: str | Path,
    *,
    processor: UnicodeFileProcessor | None = None,
    **kwargs: Any,
) -> pd.DataFrame:
    """Asynchronously read a fixed-width file and sanitize Unicode."""
    return await asyncio.to_thread(read_fwf, path, processor=processor, **kwargs)


__all__ = [
    "async_read_csv",
    "async_read_excel",
    "async_read_json",
    "async_read_parquet",
    "async_read_fwf",
]
