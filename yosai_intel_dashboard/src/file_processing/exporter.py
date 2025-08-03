from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict

import pandas as pd

from yosai_intel_dashboard.src.core.container import get_unicode_processor
from yosai_intel_dashboard.src.core.protocols import UnicodeProcessorProtocol
from yosai_intel_dashboard.src.infrastructure.callbacks.events import CallbackEvent
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import (
    TrulyUnifiedCallbacks,
)

from .column_mapper import REQUIRED_COLUMNS


class ExportError(Exception):
    """Raised when export cannot proceed."""


def _validate_columns(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ExportError(f"Missing required columns: {missing}")


EXPORT_ROOT = Path(os.getenv("EXPORT_ROOT", "exports")).resolve()


def _sanitize_path(path: str) -> Path:
    candidate = (EXPORT_ROOT / path).resolve()
    if not str(candidate).startswith(str(EXPORT_ROOT)):
        raise ExportError("Invalid export path")
    if candidate.parent != EXPORT_ROOT:
        candidate.parent.mkdir(parents=True, exist_ok=True)
    return candidate


def export_to_parquet(
    df: pd.DataFrame,
    path: str,
    meta: Dict,
    *,
    processor: UnicodeProcessorProtocol | None = None,
) -> None:
    """Export ``df`` to Parquet format with accompanying metadata.

    The dataframe is sanitized using the provided ``UnicodeProcessorProtocol``
    before being written via pandas' ``to_parquet`` method (which uses
    ``pyarrow`` under the hood). A ``.meta.json`` file containing the supplied
    ``meta`` dictionary is written alongside the Parquet file.
    """

    controller = TrulyUnifiedCallbacks()
    _validate_columns(df)
    processor = processor or get_unicode_processor()
    df_clean = processor.sanitize_dataframe(df)
    out_path = _sanitize_path(path)
    df_clean.to_parquet(out_path, index=False)
    meta_path = out_path.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    controller.trigger(
        CallbackEvent.FILE_PROCESSING_COMPLETE,
        str(out_path),
        {"export": "parquet"},
    )
