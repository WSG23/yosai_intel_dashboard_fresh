"""Async helpers for reading uploaded files."""

import asyncio
from pathlib import Path
from typing import Any

import pandas as pd

from core.config import get_max_display_rows
from services.upload.utils.file_parser import UnicodeFileProcessor
from utils.pandas_readers import read_csv, read_excel, read_json, read_parquet


class AsyncUploadProcessor:
    """Asynchronous helpers for reading uploaded files."""

    def __init__(self) -> None:
        self.unicode_processor = UnicodeFileProcessor()

    async def read_csv(self, path: str | Path, **kwargs: Any) -> pd.DataFrame:
        return await asyncio.to_thread(
            read_csv, path, processor=self.unicode_processor, **kwargs
        )

    async def read_excel(self, path: str | Path, **kwargs: Any) -> pd.DataFrame:
        return await asyncio.to_thread(
            read_excel, path, processor=self.unicode_processor, **kwargs
        )

    async def read_json(self, path: str | Path, **kwargs: Any) -> pd.DataFrame:
        return await asyncio.to_thread(
            read_json, path, processor=self.unicode_processor, **kwargs
        )

    async def read_parquet(self, path: str | Path, **kwargs: Any) -> pd.DataFrame:
        return await asyncio.to_thread(
            read_parquet, path, processor=self.unicode_processor, **kwargs
        )

    async def preview_from_parquet(
        self, path: str | Path, *, rows: int | None = None
    ) -> pd.DataFrame:
        """Return the first ``rows`` of a parquet file asynchronously."""
        df = await self.read_parquet(path)
        limit = rows or get_max_display_rows()
        return df.head(limit)


__all__ = ["AsyncUploadProcessor"]
