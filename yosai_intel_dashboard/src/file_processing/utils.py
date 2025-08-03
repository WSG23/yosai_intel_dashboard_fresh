from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any, Dict, Iterable

import chardet
import pandas as pd

from yosai_intel_dashboard.src.core.config import get_max_display_rows
from yosai_intel_dashboard.src.core.performance_file_processor import (
    PerformanceFileProcessor,
)
from yosai_intel_dashboard.src.core.unicode import (
    UnicodeProcessor,
    safe_format_number,
    safe_unicode_decode,
    sanitize_for_utf8,
)
from yosai_intel_dashboard.src.infrastructure.config.constants import DEFAULT_CHUNK_SIZE
from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import (
    dynamic_config,
)

logger = logging.getLogger(__name__)


def safe_decode_content(content: bytes) -> str:
    """Return ``content`` decoded with best-effort encoding detection."""
    try:
        detected = chardet.detect(content)
        encoding = detected.get("encoding") or "utf-8"
        return safe_unicode_decode(content, encoding)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Unicode decode error: %s", exc)
        return safe_unicode_decode(content, "latin-1")


def sanitize_dataframe_unicode(
    df: pd.DataFrame,
    *,
    chunk_size: int | None = None,
    stream: bool = False,
) -> pd.DataFrame | Iterable[pd.DataFrame]:
    """Return ``df`` sanitized for unsafe Unicode characters."""
    if chunk_size is None:
        chunk_size = getattr(dynamic_config.analytics, "chunk_size", DEFAULT_CHUNK_SIZE)

    obj_cols = list(df.select_dtypes(include=["object"]).columns)

    if not obj_cols:
        if stream:

            def _gen() -> Iterable[pd.DataFrame]:
                for start in range(0, len(df), chunk_size):
                    yield df.iloc[start : start + chunk_size]

            return _gen()
        return df

    def _generator() -> Iterable[pd.DataFrame]:
        for start in range(0, len(df), chunk_size):
            chunk = df.iloc[start : start + chunk_size].copy()
            for col in obj_cols:
                chunk[col] = chunk[col].astype(str).map(UnicodeProcessor.clean_text)
            yield chunk

    if stream:
        return _generator()

    cleaned = list(_generator())
    return pd.concat(cleaned, ignore_index=True) if cleaned else pd.DataFrame()


def read_large_csv(
    file_path: str | Path | io.TextIOBase,
    *,
    encoding: str = "utf-8",
    chunk_size: int | None = None,
    max_memory_mb: int | None = None,
    stream: bool = False,
) -> pd.DataFrame | Iterable[pd.DataFrame]:
    """Load a potentially huge CSV file via :class:`PerformanceFileProcessor`."""
    if chunk_size is None:
        chunk_size = getattr(dynamic_config.analytics, "chunk_size", DEFAULT_CHUNK_SIZE)

    processor = PerformanceFileProcessor(
        chunk_size=chunk_size, max_memory_mb=max_memory_mb
    )
    return processor.process_large_csv(file_path, encoding=encoding, stream=stream)


def create_file_preview(
    df: pd.DataFrame, max_rows: int | None = None
) -> Dict[str, Any]:
    """Return a sanitized preview of ``df`` for display."""
    try:
        limit = get_max_display_rows()
        rows = min(max_rows if max_rows is not None else limit, limit)
        preview_df = df.head(rows)

        preview_data = []
        for _, row in preview_df.iterrows():
            safe_row: Dict[str, Any] = {}
            for col, val in row.items():
                if pd.isna(val):
                    safe_row[col] = None
                elif isinstance(val, (int, float)):
                    safe_row[col] = safe_format_number(val)
                else:
                    safe_row[col] = sanitize_for_utf8(str(val))
            preview_data.append(safe_row)

        return {
            "preview_data": preview_data,
            "columns": list(df.columns),
            "total_rows": len(df),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        }
    except Exception as exc:  # pragma: no cover - best effort
        logger.error("Preview creation error: %s", exc)
        return {"preview_data": [], "columns": [], "total_rows": 0, "dtypes": {}}


__all__ = [
    "safe_decode_content",
    "sanitize_dataframe_unicode",
    "read_large_csv",
    "create_file_preview",
]
