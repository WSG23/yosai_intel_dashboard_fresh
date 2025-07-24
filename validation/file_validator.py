from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Iterable, Tuple

from config.dynamic_config import dynamic_config

from .core import ValidationResult
from .rules import CompositeValidator, ValidationRule


class FileSizeRule(ValidationRule):
    def __init__(self, max_bytes: int) -> None:
        self.max_bytes = max_bytes

    def validate(self, data: Tuple[str, bytes]) -> ValidationResult:
        filename, content = data
        if len(content) > self.max_bytes:
            return ValidationResult(False, data, ["file_too_large"])
        return ValidationResult(True, data)


class ExtensionRule(ValidationRule):
    def __init__(self, allowed: Iterable[str]) -> None:
        self.allowed = {e.lower() for e in allowed}

    def validate(self, data: Tuple[str, bytes]) -> ValidationResult:
        filename, content = data
        ext = Path(filename).suffix.lower()
        if ext not in self.allowed:
            return ValidationResult(False, data, ["invalid_extension"])
        return ValidationResult(True, data)


class CSVFormulaRule(ValidationRule):
    """Detect potential spreadsheet injection payloads."""

    def validate(self, data: Tuple[str, bytes]) -> ValidationResult:
        filename, content = data
        if Path(filename).suffix.lower() != ".csv":
            return ValidationResult(True, data)
        text = content.decode("utf-8", errors="ignore")
        reader = csv.reader(io.StringIO(text))
        try:
            for row in reader:
                for cell in row:
                    if cell.startswith(("=", "+", "-", "@")):
                        return ValidationResult(False, data, ["formula_injection"])
        except csv.Error:
            return ValidationResult(False, data, ["csv_error"])
        return ValidationResult(True, data)


class FileValidator(CompositeValidator):
    """High level file validator based on configurable rules."""

    def __init__(self, max_size_mb: int | None = None, allowed_ext: Iterable[str] | None = None) -> None:
        size_mb = max_size_mb if max_size_mb is not None else getattr(
            dynamic_config.security, "max_upload_mb", 10
        )
        size = size_mb * 1024 * 1024
        default_types = getattr(dynamic_config, "upload", None)
        if default_types and hasattr(default_types, "allowed_file_types"):
            defaults = default_types.allowed_file_types
        else:
            defaults = [".csv", ".json", ".xlsx", ".xls"]
        allowed = allowed_ext or defaults
        rules = [
            FileSizeRule(size),
            ExtensionRule(allowed),
            CSVFormulaRule(),
        ]
        super().__init__(rules)

    def validate_file_upload(self, filename: str, content: bytes) -> dict:
        result = self.validate((filename, content))
        if not result.valid:
            return {"valid": False, "issues": result.issues or []}
        size_mb = len(content) / (1024 * 1024)
        return {"valid": True, "filename": filename, "size_mb": size_mb}
