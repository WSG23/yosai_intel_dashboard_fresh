from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict

import pandas as pd

from yosai_intel_dashboard.src.infrastructure.callbacks.events import CallbackEvent
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks
from yosai_intel_dashboard.src.core.container import get_unicode_processor
from yosai_intel_dashboard.src.core.interfaces.protocols import UnicodeProcessorProtocol

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


def export_to_csv(
    df: pd.DataFrame,
    path: str,
    meta: Dict,
    *,
    processor: UnicodeProcessorProtocol | None = None,
) -> None:
    controller = TrulyUnifiedCallbacks()
    _validate_columns(df)
    processor = processor or get_unicode_processor()
    df_clean = processor.sanitize_dataframe(df)
    out_path = _sanitize_path(path)
    df_clean.to_csv(out_path, index=False, encoding="utf-8-sig")
    meta_path = out_path.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    controller.trigger(
        CallbackEvent.FILE_PROCESSING_COMPLETE,
        str(out_path),
        {"export": "csv"},
    )


def export_to_json(
    df: pd.DataFrame,
    path: str,
    meta: Dict,
    *,
    processor: UnicodeProcessorProtocol | None = None,
) -> None:
    controller = TrulyUnifiedCallbacks()
    _validate_columns(df)
    processor = processor or get_unicode_processor()
    df_clean = processor.sanitize_dataframe(df)
    out_path = _sanitize_path(path)
    out_path.write_text(
        df_clean.to_json(orient="records", force_ascii=False), encoding="utf-8"
    )
    meta_path = out_path.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    controller.trigger(
        CallbackEvent.FILE_PROCESSING_COMPLETE,
        str(out_path),
        {"export": "json"},
    )
