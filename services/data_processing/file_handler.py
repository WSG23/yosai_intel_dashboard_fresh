"""Unified file validation and security handling."""

from pathlib import Path
from typing import Any, Optional

import pandas as pd

from services.data_processing.unified_file_validator import safe_decode_with_unicode_handling
from security.unicode_security_processor import (
    sanitize_unicode_input,
    sanitize_dataframe,
)
from core.unicode_processor import process_large_csv_content
from core.callback_controller import (
    CallbackController,
    CallbackEvent,
)
from config.dynamic_config import dynamic_config


from typing import Any, Optional, Tuple

import pandas as pd

from services.input_validator import ValidationResult
from services.data_processing.unified_file_validator import UnifiedFileValidator
from services.data_processing.core.exceptions import (
    FileProcessingError,
    FileValidationError,
)



def process_file_simple(content: bytes, filename: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Parse a CSV ``content`` and return a sanitized ``DataFrame``.

    The helper intentionally performs only minimal validation and is used by
    older parts of the code base that expect a best-effort CSV reader.  It
    should **not** raise exceptions on parsing errors.  Instead a tuple of
    ``(df, None)`` is returned on success or ``(None, error_message)`` on
    failure.
    """

    if not content:
        return None, "File is empty"

    try:
        encoding = "utf-8"
        chunk_size = getattr(dynamic_config.analytics, "chunk_size", 50000)

        if len(content) > chunk_size:
            text = process_large_csv_content(content, encoding, chunk_size=chunk_size)
        else:
            text = safe_decode_with_unicode_handling(content, encoding)

        text = sanitize_unicode_input(text)

        from io import StringIO

        df = pd.read_csv(StringIO(text))
        df = sanitize_dataframe(df)
        return df, None
    except Exception as exc:  # pragma: no cover - robustness
        return None, str(exc)


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
        return self.validator.validate_file(contents, filename)


__all__ = [
    "FileHandler",
    "ValidationResult",
    "FileProcessingError",
    "process_file_simple",

]

