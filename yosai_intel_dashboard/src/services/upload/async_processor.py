from pathlib import Path
from typing import Any

import pandas as pd

from yosai_intel_dashboard.src.core.config_helpers import get_max_display_rows
from yosai_intel_dashboard.src.services.upload.utils.file_parser import UnicodeFileProcessor
from yosai_intel_dashboard.src.utils.async_pandas_readers import (
    async_read_csv,
    async_read_excel,
    async_read_json,
    async_read_parquet,
)


class AsyncUploadProcessor:
    """Asynchronous helpers for reading uploaded files."""

    def __init__(self) -> None:
        self.unicode_processor = UnicodeFileProcessor()

    async def read_csv(self, path: str | Path, **kwargs: Any) -> pd.DataFrame:
        return await async_read_csv(path, processor=self.unicode_processor, **kwargs)

    async def read_excel(self, path: str | Path, **kwargs: Any) -> pd.DataFrame:
        return await async_read_excel(path, processor=self.unicode_processor, **kwargs)

    async def read_json(self, path: str | Path, **kwargs: Any) -> pd.DataFrame:
        return await async_read_json(path, processor=self.unicode_processor, **kwargs)

    async def read_parquet(self, path: str | Path, **kwargs: Any) -> pd.DataFrame:
        return await async_read_parquet(
            path, processor=self.unicode_processor, **kwargs
        )

    async def preview_from_parquet(
        self, path: str | Path, *, rows: int | None = None
    ) -> pd.DataFrame:
        """Return the first ``rows`` of a parquet file asynchronously."""
        df = await self.read_parquet(path)
        limit = rows or get_max_display_rows()
        return df.head(limit)


__all__ = ["AsyncUploadProcessor"]
