#!/usr/bin/env python3
"""File processor that streams CSV data without imposing row limits."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List

import pandas as pd

from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import dynamic_config
from core.performance import get_performance_monitor
from unicode_toolkit import safe_encode_text

logger = logging.getLogger(__name__)


class UnlimitedFileProcessor:
    """Read CSV files in chunks and log progress."""

    def __init__(self, chunk_size: int | None = None) -> None:
        self.chunk_size = chunk_size or dynamic_config.analytics.chunk_size
        self.max_memory_mb = dynamic_config.analytics.max_memory_mb

    def read_csv_chunks(
        self, file_path: str | Path, encoding: str = "utf-8"
    ) -> Iterable[pd.DataFrame]:
        """Yield ``DataFrame`` chunks from ``file_path``."""
        path = Path(file_path)
        rows = 0
        monitor = get_performance_monitor()
        for chunk in pd.read_csv(path, chunksize=self.chunk_size, encoding=encoding):
            monitor.throttle_if_needed()
            rows += len(chunk)
            check_memory_limit(self.max_memory_mb, logger)
            logger.debug(
                "Processed %s rows from %s",
                rows,
                safe_encode_text(path.name),
            )
            yield chunk
        logger.info(
            "Finished processing %s rows from %s",
            rows,
            safe_encode_text(path.name),
        )

    def load_csv(self, file_path: str | Path, encoding: str = "utf-8") -> pd.DataFrame:
        """Return the combined dataframe from all chunks."""
        chunks: List[pd.DataFrame] = list(self.read_csv_chunks(file_path, encoding))
        if chunks:
            df = pd.concat(chunks, ignore_index=True)
        else:
            df = pd.DataFrame()
        self.validate_no_truncation(file_path, len(df))
        return df

    def validate_no_truncation(
        self, file_path: str | Path, processed_rows: int
    ) -> bool:
        """Check ``file_path`` line count matches ``processed_rows``."""
        try:
            with open(file_path, "rb") as fh:
                total_lines = sum(1 for _ in fh)
            # subtract header line
            expected = max(total_lines - 1, 0)
            if expected != processed_rows:
                logger.warning(
                    "Possible truncation reading %s: expected %s rows, got %s",
                    safe_encode_text(str(file_path)),
                    expected,
                    processed_rows,
                )
                return False
            return True
        except Exception as exc:  # pragma: no cover - validation best effort
            logger.error(
                "Validation failed for %s: %s",
                safe_encode_text(str(file_path)),
                exc,
            )
            return False


unlimited_processor = UnlimitedFileProcessor()

__all__ = ["UnlimitedFileProcessor", "unlimited_processor"]
