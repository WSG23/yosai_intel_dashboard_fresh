"""High level validator combining security and size checks."""

from __future__ import annotations

import pandas as pd
from typing import Any, Optional

from services.input_validator import InputValidator, ValidationResult
from security.file_validator import SecureFileValidator
from security.validation_exceptions import ValidationError


class UnifiedFileValidator:
    """Validate uploaded files with security and size limits."""

    def __init__(self, max_size_mb: Optional[int] = None) -> None:
        self.basic_validator = InputValidator(max_size_mb)
        self.secure_validator = SecureFileValidator()

    def sanitize_filename(self, filename: str) -> str:
        return self.secure_validator.sanitize_filename(filename)

    def validate_file_upload(self, file_obj: Any) -> ValidationResult:
        return self.basic_validator.validate_file_upload(file_obj)

    def process_base64_contents(self, contents: str, filename: str) -> pd.DataFrame:
        sanitized = self.secure_validator.sanitize_filename(filename)
        df = self.secure_validator.validate_file_contents(contents, sanitized)
        result = self.basic_validator.validate_file_upload(df)
        if not result.valid:
            raise ValidationError(result.message)
        return df


__all__ = ["UnifiedFileValidator", "ValidationResult"]
