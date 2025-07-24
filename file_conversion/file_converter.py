"""Conversion helpers for .pkl DataFrames to .parquet with Unicode cleanup."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

import pandas as pd

from core.unicode import sanitize_dataframe

_logger = logging.getLogger(__name__)


class FileConverter:
    """Utility class for converting pickled DataFrames to Parquet."""

    @staticmethod
    def pkl_to_parquet(pkl_path: Path, parquet_path: Path) -> Tuple[bool, str]:
        """Convert ``pkl_path`` DataFrame to ``parquet_path`` removing surrogates."""
        try:
            if not pkl_path.exists():
                return False, f"Pickle file not found: {pkl_path}"
            df = pd.read_pickle(pkl_path)
            df = sanitize_dataframe(df)
            parquet_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(parquet_path, index=False)
            return True, f"Converted {pkl_path} to {parquet_path}"
        except Exception as exc:  # pragma: no cover - best effort
            _logger.error("Conversion failed: %s", exc)
            return False, str(exc)


__all__ = ["FileConverter"]
