"""Input validation helpers for uploaded files.

This module provides a small helper used by :class:`AnalyticsService`
to validate uploaded files before any processing occurs.  Each file is
checked for presence, non-empty content and that its size does not
exceed configured limits.  The validator returns a simple dataclass
:class:`ValidationResult` summarizing the outcome.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional
import base64
import re

from config.dynamic_config import dynamic_config


@dataclass
class ValidationResult:
    """Result of validating an uploaded file."""

    valid: bool
    message: str = ""


class InputValidator:
    """Validate basic properties of uploaded files."""

    def __init__(self, max_size_mb: Optional[int] = None) -> None:
        self.max_size_mb = max_size_mb or dynamic_config.security.max_upload_mb

    _DATA_URI_RE = re.compile(r"^data:.*;base64,", re.IGNORECASE)

    def validate_file_upload(self, file_obj: Any) -> ValidationResult:
        """Validate an uploaded file-like object.

        Parameters
        ----------
        file_obj:
            The uploaded object which may be a :class:`~pandas.DataFrame`, a path
            to a file or bytes-like data.
        """
        if file_obj is None:
            return ValidationResult(False, "No file provided")

        # If it's a pandas DataFrame
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

        # If it's a path on disk or base64 encoded string
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

        # Raw bytes
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

        # Unknown type - treat as invalid
        return ValidationResult(False, "Unsupported file type")
