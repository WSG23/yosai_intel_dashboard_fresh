"""FileProcessor for reading and validating uploaded files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional
import logging

import pandas as pd

from services.input_validator import InputValidator, ValidationResult
from security.file_validator import SecureFileValidator
from security.dataframe_validator import DataFrameSecurityValidator
from security.validation_exceptions import ValidationError

logger = logging.getLogger(__name__)


class UnifiedFileValidator:
    """Combine file and DataFrame validation helpers."""

    def __init__(self, max_size_mb: Optional[int] = None) -> None:
        self.input_validator = InputValidator(max_size_mb)
        self.secure_validator = SecureFileValidator()
        self.df_validator = DataFrameSecurityValidator()

    # ------------------------------------------------------------------
    # Basic helpers
    # ------------------------------------------------------------------
    def validate_path(self, path: Path) -> None:
        result = self.input_validator.validate_file_upload(path)
        if not result.valid:
            raise ValidationError(result.message)

    def _read_path(self, path: Path) -> pd.DataFrame:
        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path)
        elif path.suffix.lower() == ".json":
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
            df = pd.DataFrame(data)
        elif path.suffix.lower() in {".xlsx", ".xls"}:
            df = pd.read_excel(path)
        else:
            raise ValidationError(f"Unsupported file type: {path.suffix}")
        return df

    def load_dataframe(self, path: Path) -> pd.DataFrame:
        self.validate_path(path)
        df = self._read_path(path)
        df = self.df_validator.validate_for_upload(df)
        return df

    def validate_contents(self, contents: str, filename: str) -> pd.DataFrame:
        df = self.secure_validator.validate_file_contents(contents, filename)
        result = self.input_validator.validate_file_upload(df)
        if not result.valid:
            raise ValidationError(result.message)
        df = self.df_validator.validate_for_upload(df)
        return df


class FileProcessor:
    """High level processor that delegates to :class:`UnifiedFileValidator`."""

    def __init__(self, validator: Optional[UnifiedFileValidator] = None) -> None:
        self.validator = validator or UnifiedFileValidator()

    def process_path(self, file_path: str | Path) -> pd.DataFrame:
        path = Path(file_path)
        logger.info("Processing file %s", path)
        return self.validator.load_dataframe(path)

    def process_uploaded_contents(self, contents: str, filename: str) -> pd.DataFrame:
        logger.info("Processing uploaded contents for %s", filename)
        return self.validator.validate_contents(contents, filename)

    def health_check(self) -> dict[str, Any]:
        return {"status": "ok"}


__all__ = ["FileProcessor", "UnifiedFileValidator"]
