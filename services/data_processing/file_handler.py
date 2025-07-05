import io
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Sequence

import pandas as pd

from utils.file_validator import safe_decode_with_unicode_handling
from utils.unicode_utils import (
    sanitize_unicode_input,
    sanitize_dataframe,
    process_large_csv_content,
)
from callback_controller import CallbackController, CallbackEvent
from config.dynamic_config import dynamic_config

logger = logging.getLogger(__name__)


class FileProcessingError(Exception):
    """Raised when file processing fails."""


class FileHandler:
    """Unified file processing and validation service."""

    ALLOWED_EXTENSIONS = {".csv", ".json", ".xlsx", ".xls"}
    ENCODING_PRIORITY = [
        "utf-8",
        "utf-8-sig",
        "utf-16",
        "utf-16-le",
        "utf-16-be",
        "latin1",
        "cp1252",
        "iso-8859-1",
        "ascii",
    ]
    CSV_OPTIONS: Dict[str, Any] = {
        "low_memory": False,
        "dtype": str,
        "keep_default_na": False,
        "na_filter": False,
        "skipinitialspace": True,
    }

    def __init__(self, controller: Optional[CallbackController] = None) -> None:
        self.controller = controller or CallbackController()
        self.max_size_mb = dynamic_config.get_max_upload_size_mb()

    # ------------------------------------------------------------------
    # Core API
    # ------------------------------------------------------------------
    def validate_and_decode(self, filename: str, content: bytes) -> Tuple[str, Dict[str, Any]]:
        """Validate ``content`` and return decoded text with metadata."""
        filename = sanitize_unicode_input(filename)
        ext = Path(filename).suffix.lower()
        size_mb = len(content) / (1024 * 1024)
        issues = []

        if ext not in self.ALLOWED_EXTENSIONS:
            issues.append(f"File type {ext} not allowed")
        if size_mb > self.max_size_mb:
            issues.append(
                f"File too large: {size_mb:.1f}MB > {self.max_size_mb}MB"
            )
        if len(content) == 0:
            issues.append("File is empty")

        decoded = self._decode_with_fallback(content)
        return decoded, {
            "valid": len(issues) == 0,
            "issues": issues,
            "size_mb": size_mb,
            "extension": ext,
        }

    def parse_file_content(self, content: bytes, filename: str) -> pd.DataFrame:
        """Parse ``content`` according to ``filename`` extension."""
        text, meta = self.validate_and_decode(filename, content)
        if not meta["valid"]:
            raise FileProcessingError("; ".join(meta["issues"]))

        ext = meta["extension"]
        self.controller.fire_event(
            CallbackEvent.FILE_PROCESSING_START, "file_handler", {"filename": filename}
        )
        try:
            if ext == ".csv":
                df = self._parse_csv(text)
            elif ext == ".json":
                df = self._parse_json(text)
            elif ext in {".xlsx", ".xls"}:
                df = self._parse_excel(content)
            else:
                raise FileProcessingError(f"Unsupported file type: {ext}")
            df = sanitize_dataframe(df)
            self.controller.fire_event(
                CallbackEvent.FILE_PROCESSING_COMPLETE,
                "file_handler",
                {"rows": len(df), "columns": len(df.columns)},
            )
            return df
        except Exception as exc:
            self.controller.fire_event(
                CallbackEvent.FILE_PROCESSING_ERROR,
                "file_handler",
                {"error": str(exc)},
            )
            raise FileProcessingError(str(exc)) from exc

    # ------------------------------------------------------------------
    # Decoding helpers
    # ------------------------------------------------------------------
    def _decode_with_fallback(self, content: bytes) -> str:
        for enc in self.ENCODING_PRIORITY:
            try:
                text = safe_decode_with_unicode_handling(content, enc)
                if self._is_reasonable_text(text):
                    logger.debug("Decoded content using %s", enc)
                    return text
            except Exception:
                continue
        logger.warning("All encodings failed, using replacement characters")
        return content.decode("utf-8", errors="replace")

    def _is_reasonable_text(self, text: str) -> bool:
        if not text.strip():
            return False
        replacement_ratio = text.count("\ufffd") / len(text)
        if replacement_ratio > 0.1:
            return False
        printable = sum(1 for c in text if c.isprintable() or c.isspace())
        return (printable / len(text)) > 0.7

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------
    def _parse_csv(self, text: str) -> pd.DataFrame:
        if len(text) > 10 * 1024 * 1024:
            text = process_large_csv_content(text.encode("utf-8"))
        delimiters = [",", ";", "\t", "|"]
        for delim in delimiters:
            try:
                df = pd.read_csv(io.StringIO(text), sep=delim, **self.CSV_OPTIONS)
                if len(df.columns) > 1 or (len(df.columns) == 1 and len(df) > 0):
                    return df
            except Exception:
                continue
        df = pd.read_csv(
            io.StringIO(text), engine="python", sep=None, **self.CSV_OPTIONS
        )
        return df

    def _parse_json(self, text: str) -> pd.DataFrame:
        data = json.loads(text)
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            raise FileProcessingError("JSON must be an object or array")
        return df

    def _parse_excel(self, content: bytes) -> pd.DataFrame:
        return pd.read_excel(io.BytesIO(content), dtype=str, keep_default_na=False)

    # ------------------------------------------------------------------
    # DataFrame utilities
    # ------------------------------------------------------------------
    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
        empty_ratio = float(df.isna().mean().mean()) if not df.empty else 0.0
        return {
            "valid": True,
            "rows": len(df),
            "columns": len(df.columns),
            "empty_ratio": empty_ratio,
            "column_names": list(df.columns),
        }

    def _fuzzy_match_columns(
        self, available_columns: Sequence[str], required_columns: Sequence[str]
    ) -> Dict[str, str]:
        suggestions: Dict[str, str] = {}
        mapping_patterns = {
            "person_id": [
                "person id",
                "userid",
                "user id",
                "user",
                "employee",
                "badge",
                "card",
                "person",
                "emp",
                "employee_id",
                "badge_id",
                "card_id",
            ],
            "door_id": [
                "device name",
                "devicename",
                "device_name",
                "door",
                "reader",
                "device",
                "access_point",
                "gate",
                "entry",
                "door_name",
                "reader_id",
                "access_device",
            ],
            "access_result": [
                "access result",
                "accessresult",
                "access_result",
                "result",
                "status",
                "outcome",
                "decision",
                "success",
                "granted",
                "denied",
                "access_status",
            ],
            "timestamp": [
                "timestamp",
                "time",
                "datetime",
                "date",
                "when",
                "occurred",
                "event_time",
                "access_time",
                "date_time",
                "event_date",
            ],
        }
        available_lower = {col.lower(): col for col in available_columns}
        for required_col, patterns in mapping_patterns.items():
            best_match = None
            for pattern in patterns:
                if pattern.lower() in available_lower:
                    best_match = available_lower[pattern.lower()]
                    break
            if not best_match:
                for pattern in patterns:
                    for available_col_lower, original_col in available_lower.items():
                        if pattern in available_col_lower or available_col_lower in pattern:
                            best_match = original_col
                            break
                    if best_match:
                        break
            if best_match:
                suggestions[required_col] = best_match
        return suggestions

    def apply_manual_mapping(
        self, df: pd.DataFrame, column_mapping: Dict[str, str]
    ) -> pd.DataFrame:
        missing_source_cols = [
            source for source in column_mapping.values() if source not in df.columns
        ]
        if missing_source_cols:
            raise ValueError(f"Source columns not found: {missing_source_cols}")
        return df.rename(columns={v: k for k, v in column_mapping.items()})

    def get_mapping_suggestions(self, df: pd.DataFrame) -> Dict[str, Any]:
        required_columns = ["person_id", "door_id", "access_result", "timestamp"]
        fuzzy_matches = self._fuzzy_match_columns(list(df.columns), required_columns)
        return {
            "available_columns": list(df.columns),
            "required_columns": required_columns,
            "suggested_mappings": fuzzy_matches,
            "missing_mappings": [
                col for col in required_columns if col not in fuzzy_matches
            ],
        }


# Convenience wrapper for backward compatibility

def process_file_simple(content: bytes, filename: str) -> Tuple[pd.DataFrame, Optional[str]]:
    handler = FileHandler()
    try:
        df = handler.parse_file_content(content, filename)
        return df, None
    except Exception as exc:  # pragma: no cover - best effort
        return pd.DataFrame(), str(exc)


__all__ = ["FileHandler", "process_file_simple", "FileProcessingError"]

