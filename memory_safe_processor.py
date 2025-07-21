from __future__ import annotations

import io
import logging
from typing import IO, Iterable, Union

import pandas as pd

from utils.memory_utils import check_memory_limit
from config.constants import DEFAULT_CHUNK_SIZE


logger = logging.getLogger(__name__)


class FileProcessor:
    """Process CSV files in chunks while guarding memory usage."""

    def __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE, *, max_memory_mb: int = 500) -> None:
        self.chunk_size = chunk_size
        self.max_memory_mb = max_memory_mb

    def read_large_csv(self, file_like: Union[str, IO[str]]) -> pd.DataFrame:
        """Read ``file_like`` in chunks and concatenate safely."""
        reader = pd.read_csv(file_like, chunksize=self.chunk_size)
        chunks: list[pd.DataFrame] = []
        for chunk in reader:
            check_memory_limit(self.max_memory_mb, logger)
            chunks.append(chunk)
        return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()


__all__ = ["FileProcessor"]
