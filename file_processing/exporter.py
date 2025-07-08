from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import pandas as pd

from core.callback_controller import CallbackEvent
from core.callback_manager import CallbackManager
from core.container import get_unicode_processor
from core.protocols import UnicodeProcessorProtocol
from .column_mapper import REQUIRED_COLUMNS


class ExportError(Exception):
    """Raised when export cannot proceed."""


def _validate_columns(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ExportError(f"Missing required columns: {missing}")


def export_to_csv(
    df: pd.DataFrame,
    path: str,
    meta: Dict,
    *,
    processor: UnicodeProcessorProtocol | None = None,
) -> None:
    controller = CallbackManager()
    _validate_columns(df)
    processor = processor or get_unicode_processor()
    df_clean = processor.sanitize_dataframe(df)
    out_path = Path(path)
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
    controller = CallbackManager()
    _validate_columns(df)
    processor = processor or get_unicode_processor()
    df_clean = processor.sanitize_dataframe(df)
    out_path = Path(path)
    out_path.write_text(df_clean.to_json(orient="records", force_ascii=False), encoding="utf-8")
    meta_path = out_path.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    controller.trigger(
        CallbackEvent.FILE_PROCESSING_COMPLETE,
        str(out_path),
        {"export": "json"},
    )

