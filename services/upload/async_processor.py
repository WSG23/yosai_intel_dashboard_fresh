import asyncio
from pathlib import Path
from typing import Any

import pandas as pd

from services.upload.utils.file_parser import UnicodeFileProcessor
from core.config import get_max_display_rows


class AsyncUploadProcessor:
    """Asynchronous helpers for reading uploaded files."""

    def __init__(self) -> None:
        self.unicode_processor = UnicodeFileProcessor()

    async def read_csv(self, path: str | Path, **kwargs: Any) -> pd.DataFrame:
        df = await asyncio.to_thread(pd.read_csv, path, **kwargs)
        return self.unicode_processor.sanitize_dataframe_unicode(df)

    async def read_excel(self, path: str | Path, **kwargs: Any) -> pd.DataFrame:
        df = await asyncio.to_thread(pd.read_excel, path, **kwargs)
        return self.unicode_processor.sanitize_dataframe_unicode(df)

    async def read_json(self, path: str | Path, **kwargs: Any) -> pd.DataFrame:
        df = await asyncio.to_thread(pd.read_json, path, **kwargs)
        return self.unicode_processor.sanitize_dataframe_unicode(df)

    async def read_parquet(self, path: str | Path, **kwargs: Any) -> pd.DataFrame:
        df = await asyncio.to_thread(pd.read_parquet, path, **kwargs)
        return self.unicode_processor.sanitize_dataframe_unicode(df)

    async def preview_from_parquet(
        self, path: str | Path, *, rows: int | None = None
    ) -> pd.DataFrame:
        """Return the first ``rows`` of a parquet file asynchronously."""
        df = await self.read_parquet(path)
        limit = rows or get_max_display_rows()
        return df.head(limit)


__all__ = ["AsyncUploadProcessor"]
