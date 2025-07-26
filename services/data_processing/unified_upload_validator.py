from __future__ import annotations

"""Unified upload validation utilities consolidating legacy validators."""

import base64
import io
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from config.dynamic_config import dynamic_config
from core.exceptions import ValidationError
from core.performance import get_performance_monitor
from core.protocols import ConfigurationProtocol
from core.unicode import UnicodeProcessor, sanitize_dataframe, sanitize_for_utf8
from upload_types import ValidationResult
from .dataframe_utils import process_dataframe
from utils.file_utils import safe_decode_with_unicode_handling


def create_config_methods(cls):
    cls.get_ai_confidence_threshold = lambda self: self.ai_threshold
    cls.get_max_upload_size_mb = lambda self: self.max_size_mb
    cls.get_upload_chunk_size = lambda self: self.chunk_size
    return cls


def common_init(self, config=None):
    self.config = config or {}
    self.max_size_mb = self.config.get("max_upload_size_mb", 100)
    self.ai_threshold = self.config.get("ai_confidence_threshold", 0.8)
    self.chunk_size = self.config.get("upload_chunk_size", 1048576)


def _lazy_string_validator() -> Any:
    """Import :class:`SecurityValidator` lazily from the new validation package."""
    from validation.security_validator import SecurityValidator as StringValidator

    return StringValidator()


SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9._\- ]{1,100}$")
ALLOWED_EXTENSIONS = {".csv", ".json", ".xlsx", ".xls"}


logger = logging.getLogger(__name__)


def safe_decode_file(contents: str) -> Optional[bytes]:
    try:
        if "," not in contents:
            return None
        _, content_string = contents.split(",", 1)
        decoded = base64.b64decode(content_string)
        if not decoded:
            return None
        return decoded
    except (base64.binascii.Error, ValueError):
        return None
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected error decoding file", exc_info=exc)
        raise


# ``process_dataframe`` is provided by :mod:`services.data_processing.common`.


def validate_dataframe_content(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty:
        return {
            "valid": False,
            "error": "DataFrame is empty",
            "issues": ["empty_dataframe"],
        }

    issues = []
    warnings = []

    if len(df.columns) == 0:
        return {
            "valid": False,
            "error": "DataFrame has no columns",
            "issues": ["no_columns"],
        }

    if len(df.columns) != len(set(df.columns)):
        issues.append("duplicate_columns")
        warnings.append("DataFrame contains duplicate column names")

    empty_columns = df.columns[df.isnull().all()].tolist()
    if empty_columns:
        issues.append("empty_columns")
        warnings.append(f"Columns with no data: {empty_columns}")

    total_cells = len(df) * len(df.columns)
    null_cells = df.isnull().sum().sum()
    empty_string_cells = (df == "").sum().sum()
    null_ratio = null_cells / total_cells if total_cells > 0 else 0
    empty_ratio = (
        (null_cells + empty_string_cells) / total_cells if total_cells > 0 else 0
    )

    if empty_ratio > 0.5:
        issues.append("high_empty_ratio")
        warnings.append(f"High percentage of empty cells: {empty_ratio:.1%}")

    suspicious_cols = [
        col
        for col in df.columns
        if any(
            prefix in str(col).lower()
            for prefix in ["=", "+", "-", "@", "cmd", "system"]
        )
    ]
    if suspicious_cols:
        issues.append("suspicious_column_names")
        warnings.append(f"Suspicious column names detected: {suspicious_cols}")

    return {
        "valid": len(issues) == 0
        or all(issue in ["empty_columns", "high_empty_ratio"] for issue in issues),
        "rows": len(df),
        "columns": len(df.columns),
        "null_ratio": null_ratio,
        "empty_ratio": empty_ratio,
        "issues": issues,
        "warnings": warnings,
        "column_names": list(df.columns),
        "memory_usage": df.memory_usage(deep=True).sum(),
    }


@create_config_methods
class UnifiedUploadValidator:
    """Combine all upload validation responsibilities into a single class."""

    ALLOWED_EXTENSIONS = ALLOWED_EXTENSIONS

    _DATA_URI_RE = re.compile(r"^data:.*;base64,", re.IGNORECASE)

    def __init__(
        self,
        max_size_mb: Optional[int] = None,
        config: ConfigurationProtocol = dynamic_config,
    ) -> None:
        common_init(self, config)
        if max_size_mb is not None:
            self.max_size_mb = max_size_mb
        self._string_validator = _lazy_string_validator()

    def _sanitize_string(self, value: str) -> str:
        cleaned = sanitize_for_utf8(str(value))
        if re.search(
            r"(<script.*?>.*?</script>|<.*?on\w+\s*=|javascript:|data:text/html|[<>])",
            cleaned,
            re.IGNORECASE | re.DOTALL,
        ):
            raise ValidationError("Potentially dangerous characters detected")
        result = self._string_validator.validate_input(cleaned, "input")
        if not result["valid"]:
            raise ValidationError("; ".join(result["issues"]))
        import bleach

        return bleach.clean(result["sanitized"], strip=True)

    # ------------------------------------------------------------------
    # Filename helpers
    # ------------------------------------------------------------------
    def sanitize_filename(self, filename: str) -> str:
        """Validate and sanitize a filename."""
        cleaned = self._sanitize_string(filename)
        cleaned = UnicodeProcessor.safe_encode_text(cleaned)

        if os.path.basename(cleaned) != cleaned:
            raise ValidationError("Path separators not allowed in filename")
        if len(cleaned) > 100:
            raise ValidationError("Filename too long")
        if not SAFE_FILENAME_RE.fullmatch(cleaned):
            raise ValidationError("Invalid filename")

        ext = Path(cleaned).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValidationError(f"Unsupported file type: {ext}")
        return cleaned

    # ------------------------------------------------------------------
    # DataFrame helpers
    # ------------------------------------------------------------------
    def validate_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Validate a :class:`~pandas.DataFrame` and return metrics."""
        metrics = validate_dataframe_content(df)
        if not metrics.get("valid", False):
            return metrics

        size_mb = df.memory_usage(deep=True).sum() / (1024 * 1024)
        if size_mb > self.max_size_mb:
            return {
                "valid": False,
                "error": f"Dataframe too large: {size_mb:.1f}MB > {self.max_size_mb}MB",
                "issues": ["too_large"],
            }
        metrics["memory_usage_mb"] = size_mb
        return metrics

    def validate_file_meta(self, filename: str, size: int) -> Dict[str, Any]:
        """Validate filename and file size without inspecting contents."""
        issues: list[str] = []
        max_bytes = self.max_size_mb * 1024 * 1024
        if size > max_bytes:
            issues.append("File too large")
        if not SAFE_FILENAME_RE.fullmatch(filename):
            issues.append("Invalid filename")
        ext = Path(filename).suffix.lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            issues.append(f"Unsupported file type: {ext}")
        return {"valid": len(issues) == 0, "issues": issues}

    # ------------------------------------------------------------------
    # File helpers
    # ------------------------------------------------------------------
    def validate_file(self, contents: str, filename: str) -> pd.DataFrame:
        """Decode ``contents`` and return a validated :class:`~pandas.DataFrame`."""
        sanitized_name = self.sanitize_filename(filename)

        file_bytes = safe_decode_file(contents)
        if file_bytes is None:
            raise ValidationError("Invalid base64 contents")

        sec_result = self.validate_file_meta(sanitized_name, len(file_bytes))
        if not sec_result["valid"]:
            raise ValidationError("; ".join(sec_result["issues"]))

        df, err = process_dataframe(file_bytes, sanitized_name, config=self.config)
        if df is None:
            raise ValidationError(err or "Unable to parse file")

        metrics = self.validate_dataframe(df)
        if not metrics.get("valid", False):
            raise ValidationError(metrics.get("error", "Invalid dataframe"))

        df = sanitize_dataframe(df)
        return df

    # ------------------------------------------------------------------
    # Compatibility helpers
    # ------------------------------------------------------------------
    def validate_file_upload(self, file_obj: Any) -> ValidationResult:
        """Validate ``file_obj`` mimicking the legacy :class:`UploadValidator`."""

        if file_obj is None:
            return ValidationResult(False, "No file provided")

        try:
            import pandas as pd

            if isinstance(file_obj, pd.DataFrame):
                if file_obj.empty:
                    return ValidationResult(False, "Empty dataframe")
                size_mb = file_obj.memory_usage(deep=True).sum() / (1024 * 1024)
                if size_mb > self.max_size_mb:
                    return ValidationResult(
                        False,
                        f"Dataframe too large: {size_mb:.1f}MB > {self.max_size_mb}MB",
                    )
                return ValidationResult(True, "ok")
        except Exception:
            pass

        if isinstance(file_obj, (str, Path)):
            text = str(file_obj)
            if self._DATA_URI_RE.match(text):
                try:
                    _, b64 = text.split(",", 1)
                    decoded = base64.b64decode(b64)
                except Exception:
                    return ValidationResult(False, "Invalid base64 contents")
                return self.validate_file_upload(decoded)

            if isinstance(file_obj, Path) or Path(text).exists():
                path = Path(file_obj)
                if not path.exists():
                    return ValidationResult(False, "File not found")
                size_mb = path.stat().st_size / (1024 * 1024)
                if size_mb == 0:
                    return ValidationResult(False, "File is empty")
                if size_mb > self.max_size_mb:
                    return ValidationResult(
                        False,
                        f"File too large: {size_mb:.1f}MB > {self.max_size_mb}MB",
                    )
                return ValidationResult(True, "ok")
            return ValidationResult(False, "File not found")

        if isinstance(file_obj, (bytes, bytearray)):
            size_mb = len(file_obj) / (1024 * 1024)
            if size_mb == 0:
                return ValidationResult(False, "File is empty")
            if size_mb > self.max_size_mb:
                return ValidationResult(
                    False,
                    f"File too large: {size_mb:.1f}MB > {self.max_size_mb}MB",
                )
            return ValidationResult(True, "ok")

        return ValidationResult(False, "Unsupported file type")

    def process_base64_contents(self, contents: str, filename: str) -> pd.DataFrame:
        """Backward compatible wrapper for :meth:`validate_file`."""
        return self.validate_file(contents, filename)


__all__ = [
    "UnifiedUploadValidator",
    "ValidationResult",
    "safe_decode_file",
    "process_dataframe",
    "validate_dataframe_content",
]
