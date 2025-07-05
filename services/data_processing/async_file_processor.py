#!/usr/bin/env python3
"""Asynchronous CSV processing helpers."""


from __future__ import annotations

import asyncio
from pathlib import Path
from typing import AsyncIterator, Callable, List, Optional

import pandas as pd

from config.dynamic_config import dynamic_config


class AsyncFileProcessor:
    """Read CSV files asynchronously in chunks with progress reporting."""

    def __init__(self, chunk_size: int | None = None) -> None:
        self.chunk_size = chunk_size or dynamic_config.analytics.chunk_size

    async def read_csv_chunks(
        self,
        file_path: str | Path,
        *,
        encoding: str = "utf-8",
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> AsyncIterator[pd.DataFrame]:
        path = Path(file_path)
        total_lines = await asyncio.to_thread(self._count_lines, path)
        processed = 0
        reader = pd.read_csv(path, chunksize=self.chunk_size, encoding=encoding)

        def _next_chunk() -> pd.DataFrame | None:
            try:
                return next(reader)
            except StopIteration:
                return None

        while True:
            chunk = await asyncio.to_thread(_next_chunk)
            if chunk is None:
                break
            processed += len(chunk)
            if progress_callback and total_lines:
                pct = int(processed / total_lines * 100)
                pct = max(0, min(100, pct))
                try:
                    progress_callback(pct)
                except Exception:  # pragma: no cover - best effort
                    pass
            yield chunk
        if progress_callback:
            try:
                progress_callback(100)
            except Exception:  # pragma: no cover - best effort
                pass

    async def load_csv(
        self,
        file_path: str | Path,
        *,
        encoding: str = "utf-8",
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> pd.DataFrame:
        chunks: List[pd.DataFrame] = []
        async for chunk in self.read_csv_chunks(
            file_path, encoding=encoding, progress_callback=progress_callback
        ):
            chunks.append(chunk)
        return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()

    @staticmethod
    def _count_lines(path: Path) -> int:
        with open(path, "rb") as fh:
            return max(sum(1 for _ in fh) - 1, 0)



__all__ = ["AsyncFileProcessor"]
