"""Asynchronous file processor using aiofiles."""

from __future__ import annotations

import asyncio
import base64
import logging
import os
from pathlib import Path
from typing import Callable, Awaitable, Optional

import aiofiles
import pandas as pd

from .file_processor import UnicodeFileProcessor

logger = logging.getLogger(__name__)


class AsyncFileProcessor:
    """Process uploaded files asynchronously in chunks."""

    def __init__(self, chunk_size: int = 1024 * 1024) -> None:
        self.chunk_size = chunk_size

    async def _notify(
        self,
        callback: Optional[Callable[[str, int], Awaitable[None] | None]],
        filename: str,
        processed: int,
        total: int,
    ) -> None:
        if not callback:
            return
        percent = int(processed / total * 100) if total else 100
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(filename, percent)
            else:
                callback(filename, percent)
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("Progress callback failed: %s", exc)

    async def process_file(
        self,
        contents: str,
        filename: str,
        progress_callback: Optional[Callable[[str, int], Awaitable[None] | None]] = None,
    ) -> pd.DataFrame:
        """Return DataFrame parsed from ``contents``."""
        prefix, data = contents.split(",", 1)
        raw = base64.b64decode(data)
        total = len(raw)
        async with aiofiles.tempfile.NamedTemporaryFile(
            "wb", delete=False, suffix=Path(filename).suffix
        ) as tmp:
            path = tmp.name
            for offset in range(0, total, self.chunk_size):
                chunk = raw[offset : offset + self.chunk_size]
                await tmp.write(chunk)
                await self._notify(progress_callback, filename, offset + len(chunk), total)
        try:
            if filename.endswith(".csv"):
                df = await asyncio.to_thread(pd.read_csv, path)
            elif filename.endswith((".xlsx", ".xls")):
                df = await asyncio.to_thread(pd.read_excel, path)
            else:
                raise ValueError(f"Unsupported file type: {filename}")
        finally:
            try:
                os.unlink(path)
            except Exception:  # pragma: no cover - cleanup best effort
                pass
        df = UnicodeFileProcessor.sanitize_dataframe_unicode(df)
        await self._notify(progress_callback, filename, total, total)
        return df


__all__ = ["AsyncFileProcessor"]
