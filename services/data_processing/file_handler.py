"""Unified file validation and security handling."""

from pathlib import Path
from typing import Any, Optional

import pandas as pd

from utils.file_validator import safe_decode_with_unicode_handling
from utils.unicode_utils import (
    sanitize_unicode_input,
    sanitize_dataframe,
    process_large_csv_content,
)
from core.callback_controller import (
    CallbackController,
    CallbackEvent,
)
from config.dynamic_config import dynamic_config


from typing import Any, Optional, Tuple

import pandas as pd

from security.file_validator import SecureFileValidator
from services.input_validator import InputValidator, ValidationResult
from services.data_processing.core.exceptions import (
    FileProcessingError,
    FileValidationError,
)



def process_file_simple(content: bytes, filename: str):
    """Minimal stub for compatibility with imports."""
    raise FileProcessingError("Processing not implemented")


class FileHandler:
    """Combine security and basic validation for uploaded files."""

    def __init__(self, max_size_mb: Optional[int] = None) -> None:
        self.validator = UnifiedFileValidator(max_size_mb)

    def sanitize_filename(self, filename: str) -> str:
        return self.validator.sanitize_filename(filename)

    def validate_file_upload(self, file_obj: Any) -> ValidationResult:
        """Run basic checks on ``file_obj`` using :class:`UnifiedFileValidator`."""
        if file_obj is None:
            return ValidationResult(False, "No file provided")
        try:
            import pandas as pd
            if isinstance(file_obj, pd.DataFrame):
                metrics = self.validator.validate_dataframe(file_obj)
                return ValidationResult(metrics.get("valid", False), metrics.get("error", "ok") if not metrics.get("valid", False) else "ok")
        except Exception:
            pass
        if isinstance(file_obj, (str, Path)):
            path = Path(file_obj)
            if not path.exists():
                return ValidationResult(False, "File not found")
            size_mb = path.stat().st_size / (1024 * 1024)
            if size_mb == 0:
                return ValidationResult(False, "File is empty")
            if size_mb > self.validator.max_size_mb:
                return ValidationResult(False, f"File too large: {size_mb:.1f}MB > {self.validator.max_size_mb}MB")
            return ValidationResult(True, "ok")

        if isinstance(file_obj, (bytes, bytearray)):
            size_mb = len(file_obj) / (1024 * 1024)
            if size_mb == 0:
                return ValidationResult(False, "File is empty")
            if size_mb > self.validator.max_size_mb:
                return ValidationResult(False, f"File too large: {size_mb:.1f}MB > {self.validator.max_size_mb}MB")
            return ValidationResult(True, "ok")

        return ValidationResult(False, "Unsupported file type")

    def process_base64_contents(self, contents: str, filename: str) -> pd.DataFrame:
        """Decode ``contents`` and return a validated :class:`~pandas.DataFrame`."""
        sanitized = self.secure_validator.sanitize_filename(filename)
        df = self.secure_validator.validate_file_contents(contents, sanitized)
        result = self.basic_validator.validate_file_upload(df)
        if not result.valid:
            raise FileValidationError(result.message)

        return df


__all__ = [
    "FileHandler",
    "ValidationResult",
    "FileProcessingError",
    "process_file_simple",

]

