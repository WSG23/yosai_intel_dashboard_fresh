from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import pandas as pd

from core.callback_controller import CallbackController, CallbackEvent
from core.unicode_processor import UnicodeProcessor
from .column_mapper import REQUIRED_COLUMNS


class ExportError(Exception):
    """Raised when export cannot proceed."""


def _validate_columns(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ExportError(f"Missing required columns: {missing}")


def export_to_csv(df: pd.DataFrame, path: str, meta: Dict) -> None:
    controller = CallbackController()
    _validate_columns(df)
    df_clean = UnicodeProcessor.sanitize_dataframe(df)
    out_path = Path(path)
    df_clean.to_csv(out_path, index=False, encoding="utf-8-sig")
    meta_path = out_path.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    controller.fire_event(
        CallbackEvent.FILE_PROCESSING_COMPLETE,
        str(out_path),
        {"export": "csv"},
    )


def export_to_json(df: pd.DataFrame, path: str, meta: Dict) -> None:
    controller = CallbackController()
    _validate_columns(df)
    df_clean = UnicodeProcessor.sanitize_dataframe(df)
    out_path = Path(path)
    out_path.write_text(df_clean.to_json(orient="records", force_ascii=False), encoding="utf-8")
    meta_path = out_path.with_suffix(".meta.json")
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    controller.fire_event(
        CallbackEvent.FILE_PROCESSING_COMPLETE,
        str(out_path),
        {"export": "json"},
    )

