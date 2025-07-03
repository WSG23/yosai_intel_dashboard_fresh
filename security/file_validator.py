"""File validation utilities."""

import os
from pathlib import Path
from typing import Any

import pandas as pd

from utils.file_validator import safe_decode_file, process_dataframe
from utils.unicode_utils import sanitize_unicode_input
from config.dynamic_config import dynamic_config

from .validation_exceptions import ValidationError

class SecureFileValidator:
    """Validate uploaded files."""

    ALLOWED_EXTENSIONS = {".csv", ".json", ".xlsx", ".xls"}

    def sanitize_filename(self, filename: str) -> str:
        filename = sanitize_unicode_input(filename)
        if os.path.basename(filename) != filename:
            raise ValidationError("Path separators not allowed in filename")
        if len(filename) > 100:
            raise ValidationError("Filename too long")
        return filename

    def validate_file_contents(self, contents: str, filename: str) -> pd.DataFrame:
        result = safe_decode_file(contents)
        if result is None:
            raise ValidationError("Invalid base64 contents")
        df, err = process_dataframe(result, filename)
        if df is None:
            raise ValidationError(err or "Unable to parse file")
        return df
