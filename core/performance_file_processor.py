#!/usr/bin/env python3
"""Utilities for efficiently processing large CSV files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, List, Optional

import pandas as pd

try:
    import psutil
except ImportError:  # pragma: no cover - optional dependency
    psutil = None  # type: ignore


class PerformanceFileProcessor:
    """Process large CSV files in chunks with memory tracking."""

    def __init__(self, chunk_size: int = 50000, *, max_memory_mb: int | None = None) -> None:
        from config.dynamic_config import dynamic_config

        self.chunk_size = chunk_size
        self.logger = logging.getLogger(__name__)
        self.max_memory_mb = max_memory_mb or dynamic_config.analytics.max_memory_mb

    def process_large_csv(
        self,
        file_path: str | Path,
        *,
        encoding: str = "utf-8",
        progress_callback: Optional[Callable[[int, float], None]] = None,
    ) -> pd.DataFrame:
        """Load ``file_path`` in chunks while reporting memory usage.

        Parameters
        ----------
        file_path:
            Location of the CSV file to process.
        encoding:
            Text encoding of the file.
        progress_callback:
            Optional callable invoked after each chunk with ``rows_processed`` and
            current memory usage in MB.
        """

        path = Path(file_path)
        dfs: List[pd.DataFrame] = []
        rows = 0

        for chunk in pd.read_csv(path, chunksize=self.chunk_size, encoding=encoding):
            dfs.append(chunk)
            rows += len(chunk)
            mem_mb = (
                psutil.Process().memory_info().rss / (1024 * 1024)
                if psutil else 0
            )
            if self.max_memory_mb and mem_mb > self.max_memory_mb:
                self.logger.error(
                    "Memory usage %.1f MB exceeds limit %s MB", mem_mb, self.max_memory_mb
                )
                raise MemoryError(
                    f"Memory usage {mem_mb:.1f} MB exceeds limit {self.max_memory_mb} MB"
                )
            if progress_callback:
                try:
                    progress_callback(rows, mem_mb)
                except Exception as exc:  # pragma: no cover - defensive
                    self.logger.warning("Progress callback failed: %s", exc)

        df = pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()
        self.logger.info(
            "Processed %s rows from %s (memory %.1f MB)", rows, path, mem_mb
        )
        return df


__all__ = ["PerformanceFileProcessor"]

