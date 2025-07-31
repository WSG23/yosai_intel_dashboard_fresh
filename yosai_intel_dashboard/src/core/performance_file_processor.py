#!/usr/bin/env python3
"""Utilities for efficiently processing large CSV files."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import IO, Callable, Iterable, List, Optional, Union

import pandas as pd

from config.constants import DEFAULT_CHUNK_SIZE

try:
    import psutil
except ImportError:  # pragma: no cover - optional dependency
    psutil = None  # type: ignore


class PerformanceFileProcessor:
    """Process large CSV files in chunks with memory tracking."""

    def __init__(
        self, chunk_size: int = DEFAULT_CHUNK_SIZE, *, max_memory_mb: int | None = None
    ) -> None:
        from config.dynamic_config import dynamic_config

        self.chunk_size = chunk_size
        self.logger = logging.getLogger(__name__)
        self.max_memory_mb = max_memory_mb or dynamic_config.analytics.max_memory_mb

    def _get_memory_usage(self) -> float:
        """Return current process memory usage in MB."""
        if psutil is None:
            return 0.0
        try:
            return psutil.Process().memory_info().rss / (1024 * 1024)
        except Exception:  # pragma: no cover - best effort
            return 0.0

    def process_large_csv(
        self,
        file_path: Union[str, Path, IO[str]],
        *,
        encoding: str = "utf-8",
        progress_callback: Optional[Callable[[int, float], None]] = None,
        max_memory_mb: Optional[float] = None,
        stream: bool = False,
    ) -> pd.DataFrame | Iterable[pd.DataFrame]:
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

        handle = file_path
        if isinstance(file_path, (str, Path)):
            handle = Path(file_path)

        reader = pd.read_csv(handle, chunksize=self.chunk_size, encoding=encoding)

        def generator() -> Iterable[pd.DataFrame]:
            rows = 0
            buffer: List[pd.DataFrame] = []
            mem_mb = 0.0
            for chunk in reader:
                rows += len(chunk)
                buffer.append(chunk)
                mem_mb = self._get_memory_usage()
                if progress_callback:
                    try:
                        progress_callback(rows, mem_mb)
                    except Exception as exc:  # pragma: no cover - defensive
                        self.logger.warning(f"Progress callback failed: {exc}")

                if stream:
                    yield chunk
                    buffer.clear()
                elif max_memory_mb and mem_mb > max_memory_mb:
                    yield pd.concat(buffer, ignore_index=True)
                    buffer.clear()

            if not stream:
                if buffer:
                    yield pd.concat(buffer, ignore_index=True)
            self.logger.info(
                f"Processed {rows} rows from {file_path} (memory {mem_mb:.1f} MB)"
            )

        gen = generator()
        if stream:
            return gen
        chunks = list(gen)
        return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()


__all__ = ["PerformanceFileProcessor"]
