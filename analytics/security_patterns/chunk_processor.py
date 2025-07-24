from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

import pandas as pd

from utils.memory_utils import check_memory_limit


@dataclass
class MemoryConfig:
    """Configuration for :class:`ChunkedDataProcessor`."""

    max_memory_mb: int = 500
    chunk_size: int = 50_000


class ChunkedDataProcessor:
    """Process DataFrames in memory-safe chunks."""

    def __init__(self, config: MemoryConfig, logger: logging.Logger | None = None) -> None:
        self.config = config
        self.logger = logger or logging.getLogger(__name__)

    def process_dataframe_chunked(self, df: pd.DataFrame, func: Callable[[pd.DataFrame], Any]) -> None:
        """Apply ``func`` to ``df`` in ``chunk_size`` pieces."""
        for i in range(0, len(df), self.config.chunk_size):
            chunk = df.iloc[i : i + self.config.chunk_size]
            check_memory_limit(self.config.max_memory_mb, self.logger)
            try:
                func(chunk)
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.error("Chunk processing failed: %s", exc)
                raise


__all__ = ["ChunkedDataProcessor", "MemoryConfig"]
