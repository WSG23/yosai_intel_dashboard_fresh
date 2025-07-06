"""Validation helpers for uploaded files."""
from __future__ import annotations

import base64
import re
from pathlib import Path
from typing import Any, Optional

from config.dynamic_config import dynamic_config
from upload_types import ValidationResult


class UploadValidator:
    """Validate basic properties of uploaded files."""

    _DATA_URI_RE = re.compile(r"^data:.*;base64,", re.IGNORECASE)

    def __init__(self, max_size_mb: Optional[int] = None) -> None:
        self.max_size_mb = max_size_mb or dynamic_config.security.max_upload_mb

    def validate_file_upload(self, file_obj: Any) -> ValidationResult:
        if file_obj is None:
            return ValidationResult(False, "No file provided")

        try:
            import pandas as pd
            if isinstance(file_obj, pd.DataFrame):
                if file_obj.empty:
                    return ValidationResult(False, "Empty dataframe")
                size_mb = file_obj.memory_usage(deep=True).sum() / (1024 * 1024)
                if size_mb > self.max_size_mb:
                    return ValidationResult(False, f"Dataframe too large: {size_mb:.1f}MB > {self.max_size_mb}MB")
                return ValidationResult(True, "ok")
        except Exception:
            pass

        if isinstance(file_obj, (str, Path)):
            text = str(file_obj)
            if self._DATA_URI_RE.match(text):
                try:
                    _, b64 = text.split(',', 1)
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
                    return ValidationResult(False, f"File too large: {size_mb:.1f}MB > {self.max_size_mb}MB")
                return ValidationResult(True, "ok")
            return ValidationResult(False, "File not found")

        if isinstance(file_obj, (bytes, bytearray)):
            size_mb = len(file_obj) / (1024 * 1024)
            if size_mb == 0:
                return ValidationResult(False, "File is empty")
            if size_mb > self.max_size_mb:
                return ValidationResult(False, f"File too large: {size_mb:.1f}MB > {self.max_size_mb}MB")
            return ValidationResult(True, "ok")

        return ValidationResult(False, "Unsupported file type")
