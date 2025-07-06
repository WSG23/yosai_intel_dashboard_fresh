from __future__ import annotations

"""Unified file validation utilities consolidating legacy validators."""

from pathlib import Path
import os
import base64
import io
import json
import logging
import re
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from config.dynamic_config import dynamic_config
from core.performance import get_performance_monitor
from core.unicode import (
    UnicodeProcessor,
    sanitize_dataframe,
    sanitize_unicode_input,
)
from services.input_validator import InputValidator, ValidationResult


def _lazy_string_validator() -> "StringValidator":
    """Import ``InputValidator`` from :mod:`core.security` lazily."""
    from core.security import InputValidator as StringValidator

    return StringValidator()


from core.exceptions import ValidationError


SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9._\- ]{1,100}$")
ALLOWED_EXTENSIONS = {".csv", ".json", ".xlsx", ".xls"}


logger = logging.getLogger(__name__)


def safe_decode_with_unicode_handling(data: bytes, enc: str) -> str:
    try:
        text = data.decode(enc, errors="surrogatepass")
    except UnicodeDecodeError:
        text = data.decode(enc, errors="replace")

    text = UnicodeProcessor.clean_surrogate_chars(text)

    from security.unicode_security_handler import UnicodeSecurityHandler

    cleaned = UnicodeSecurityHandler.sanitize_unicode_input(text)
    return cleaned.replace("\ufffd", "")


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


def process_dataframe(
    decoded: bytes, filename: str
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    try:
        filename_lower = filename.lower()
        monitor = get_performance_monitor()
        chunk_size = getattr(dynamic_config.analytics, "chunk_size", 50000)

        if filename_lower.endswith(".csv"):
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    text = safe_decode_with_unicode_handling(decoded, encoding)
                    reader = pd.read_csv(
                        io.StringIO(text),
                        on_bad_lines="skip",
                        encoding="utf-8",
                        low_memory=False,
                        dtype=str,
                        keep_default_na=False,
                        chunksize=chunk_size,
                    )
                    chunks = []
                    for chunk in reader:
                        monitor.throttle_if_needed()
                        chunks.append(chunk)
                    df = (
                        pd.concat(chunks, ignore_index=True)
                        if chunks
                        else pd.DataFrame()
                    )
                    return df, None
                except UnicodeDecodeError:
                    continue
            return None, "Could not decode CSV with any standard encoding"
        elif filename_lower.endswith(".json"):
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    text = safe_decode_with_unicode_handling(decoded, encoding)
                    reader = pd.read_json(
                        io.StringIO(text),
                        lines=True,
                        chunksize=chunk_size,
                    )
                    chunks = []
                    for chunk in reader:
                        monitor.throttle_if_needed()
                        chunks.append(chunk)
                    df = (
                        pd.concat(chunks, ignore_index=True)
                        if chunks
                        else pd.DataFrame()
                    )
                    return df, None
                except UnicodeDecodeError:
                    continue
            return None, "Could not decode JSON with any standard encoding"
        elif filename_lower.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(decoded))
            return df, None
        else:
            return None, f"Unsupported file type: {filename}"
    except (
        UnicodeDecodeError,
        ValueError,
        pd.errors.ParserError,
        json.JSONDecodeError,
    ) as e:
        return None, f"Error processing file: {str(e)}"
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected error processing file", exc_info=exc)
        raise


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


class UnifiedFileValidator:
    """Combine all file validation responsibilities into a single class."""

    ALLOWED_EXTENSIONS = ALLOWED_EXTENSIONS

    def __init__(self, max_size_mb: Optional[int] = None) -> None:
        self.max_size_mb = max_size_mb or dynamic_config.security.max_upload_mb
        self._string_validator = _lazy_string_validator()
        self._basic_validator = InputValidator(self.max_size_mb)

    def _sanitize_string(self, value: str) -> str:
        cleaned = sanitize_unicode_input(str(value))
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
        cleaned = UnicodeProcessor.safe_encode(cleaned)

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

        df, err = process_dataframe(file_bytes, sanitized_name)
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
        """Validate ``file_obj`` using the basic validator."""
        return self._basic_validator.validate_file_upload(file_obj)

    def process_base64_contents(self, contents: str, filename: str) -> pd.DataFrame:
        """Backward compatible wrapper for :meth:`validate_file`."""
        return self.validate_file(contents, filename)


__all__ = [
    "UnifiedFileValidator",
    "ValidationResult",
    "safe_decode_with_unicode_handling",
    "safe_decode_file",
    "process_dataframe",
    "validate_dataframe_content",
]
