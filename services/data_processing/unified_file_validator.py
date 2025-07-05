from __future__ import annotations

"""Unified file validation utilities consolidating legacy validators."""

from pathlib import Path
import os
from typing import Any, Dict, Optional

import pandas as pd

from config.dynamic_config import dynamic_config
from utils.file_validator import (
    validate_dataframe_content,
    safe_decode_file,
    process_dataframe,
)
from utils.unicode_utils import UnicodeProcessor, sanitize_dataframe
from core.input_validation import InputValidator as StringValidator
from security.auth_service import SecurityService, SAFE_FILENAME_RE
from security.file_validator import SecureFileValidator
from security.validation_exceptions import ValidationError


class UnifiedFileValidator:
    """Combine all file validation responsibilities into a single class."""

    ALLOWED_EXTENSIONS = SecureFileValidator.ALLOWED_EXTENSIONS

    def __init__(self, max_size_mb: Optional[int] = None) -> None:
        self.max_size_mb = max_size_mb or dynamic_config.security.max_upload_mb
        self._string_validator = StringValidator()
        self._security_service = SecurityService(None)
        self._security_service.enable_file_validation()

    # ------------------------------------------------------------------
    # Filename helpers
    # ------------------------------------------------------------------
    def sanitize_filename(self, filename: str) -> str:
        """Validate and sanitize a filename."""
        cleaned = self._string_validator.validate(filename)
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

    # ------------------------------------------------------------------
    # File helpers
    # ------------------------------------------------------------------
    def validate_file(self, contents: str, filename: str) -> pd.DataFrame:
        """Decode ``contents`` and return a validated :class:`~pandas.DataFrame`."""
        sanitized_name = self.sanitize_filename(filename)

        file_bytes = safe_decode_file(contents)
        if file_bytes is None:
            raise ValidationError("Invalid base64 contents")

        sec_result = self._security_service.validate_file(sanitized_name, len(file_bytes))
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


__all__ = ["UnifiedFileValidator"]
