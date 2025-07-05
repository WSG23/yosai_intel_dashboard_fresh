"""Unified file validation and security handling."""

import io
import json
from pathlib import Path

import pandas as pd

from utils.file_validator import safe_decode_with_unicode_handling
from utils.unicode_utils import (
    sanitize_unicode_input,
    sanitize_dataframe,
    process_large_csv_content,
)
from services.data_processing.callback_controller import (
    CallbackController,
    CallbackEvent,
)
from config.dynamic_config import dynamic_config


from typing import Any, Optional, Tuple

import pandas as pd

from security.file_validator import SecureFileValidator
from services.input_validator import InputValidator, ValidationResult
from security.validation_exceptions import ValidationError
from core.error_handling import FileProcessingError


class FileHandler:
    """Combine security and basic validation for uploaded files."""

    def __init__(self, max_size_mb: Optional[int] = None) -> None:
        self.basic_validator = InputValidator(max_size_mb)
        self.secure_validator = SecureFileValidator()

    def sanitize_filename(self, filename: str) -> str:
        return self.secure_validator.sanitize_filename(filename)

    def validate_file_upload(self, file_obj: Any) -> ValidationResult:
        """Run basic checks on ``file_obj`` using :class:`InputValidator`."""
        return self.basic_validator.validate_file_upload(file_obj)

    def process_base64_contents(self, contents: str, filename: str) -> pd.DataFrame:
        """Decode ``contents`` and return a validated :class:`~pandas.DataFrame`."""
        sanitized = self.secure_validator.sanitize_filename(filename)
        df = self.secure_validator.validate_file_contents(contents, sanitized)
        result = self.basic_validator.validate_file_upload(df)
        if not result.valid:
            raise ValidationError(result.message)
        return df


def process_file_simple(content: bytes, filename: str) -> Tuple[pd.DataFrame, str | None]:
    """Lightweight helper for quickly processing small files.

    This avoids the callback system and only performs minimal validation.
    """
    try:
        filename = sanitize_unicode_input(filename)
        suffix = Path(filename).suffix.lower()

        if suffix == ".csv":
            text = safe_decode_with_unicode_handling(content, "utf-8")
            df = pd.read_csv(io.StringIO(text))
        elif suffix == ".json":
            text = safe_decode_with_unicode_handling(content, "utf-8")
            data = json.loads(text)
            df = pd.DataFrame(data)
        elif suffix in {".xlsx", ".xls"}:
            df = pd.read_excel(io.BytesIO(content))
        else:
            raise FileProcessingError(f"Unsupported file type: {suffix}")

        return sanitize_dataframe(df), None
    except Exception as exc:  # pragma: no cover - best effort
        return pd.DataFrame(), str(exc)


__all__ = [
    "FileHandler",
    "ValidationResult",
    "process_file_simple",
    "FileProcessingError",
]

