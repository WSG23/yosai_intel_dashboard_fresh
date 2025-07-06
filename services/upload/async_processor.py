import asyncio
from pathlib import Path
from typing import Any

import pandas as pd
from services.analytics_service import MAX_DISPLAY_ROWS

from services.data_processing.file_processor import UnicodeFileProcessor


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

    async def preview_from_parquet(self, path: str | Path, *, rows: int = 10) -> pd.DataFrame:
        """Return the first ``rows`` of a parquet file asynchronously."""
        df = await self.read_parquet(path)
        df_limited = df.head(MAX_DISPLAY_ROWS) if len(df) > MAX_DISPLAY_ROWS else df
        return df_limited.head(rows)


__all__ = ["AsyncUploadProcessor"]
