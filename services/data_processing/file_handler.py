"""Unified file validation and security handling."""

from pathlib import Path
from typing import Any, Optional

import pandas as pd

from services.data_processing.unified_file_validator import (
    UnifiedFileValidator,
    ValidationResult,
)
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
        return self.validator.validate_file_upload(file_obj)

    def process_base64_contents(self, contents: str, filename: str) -> pd.DataFrame:
        """Decode ``contents`` and return a validated :class:`~pandas.DataFrame`."""
        return self.validator.validate_file(contents, filename)


__all__ = [
    "FileHandler",
    "ValidationResult",
    "FileProcessingError",
    "process_file_simple",

]

