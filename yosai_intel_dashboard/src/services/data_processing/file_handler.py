"""Unified file validation and security handling."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Optional, Tuple

import pandas as pd

from config.constants import DEFAULT_CHUNK_SIZE
from config.dynamic_config import dynamic_config
from core.performance import get_performance_monitor
from core.protocols import ConfigurationProtocol
from core.unicode import (
    process_large_csv_content,
    sanitize_dataframe,
    sanitize_for_utf8,
)
from services.common.config_utils import common_init, create_config_methods
from services.data_processing.core.exceptions import (
    FileProcessingError,
    FileValidationError,
)
from services.upload.upload_types import ValidationResult
from utils.file_utils import safe_decode_with_unicode_handling
from validation.security_validator import SecurityValidator


def process_file_simple(
    content: bytes,
    filename: str,
    *,
    config: ConfigurationProtocol = dynamic_config,
) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
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
        chunk_size = getattr(config.analytics, "chunk_size", DEFAULT_CHUNK_SIZE)

        if len(content) > chunk_size:
            text = process_large_csv_content(content, encoding, chunk_size=chunk_size)
        else:
            text = safe_decode_with_unicode_handling(content, encoding)

        text = sanitize_for_utf8(text)

        from io import StringIO

        monitor = get_performance_monitor()
        reader = pd.read_csv(StringIO(text), chunksize=chunk_size)
        chunks = []
        for chunk in reader:
            monitor.throttle_if_needed()
            chunks.append(chunk)
        df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
        df = sanitize_dataframe(df)
        return df, None
    except Exception as exc:  # pragma: no cover - robustness
        return None, str(exc)


@create_config_methods
class FileHandler:
    """Combine security and basic validation for uploaded files."""

    def __init__(
        self,
        max_size_mb: Optional[int] = None,
        config: ConfigurationProtocol = dynamic_config,
    ) -> None:
        common_init(self, config)
        if max_size_mb is not None:
            self.max_size_mb = max_size_mb
        self.validator = SecurityValidator()

    def sanitize_filename(self, filename: str) -> str:
        return self.validator.sanitize_filename(filename)

    def validate_file_upload(self, file_obj: Any) -> ValidationResult:
        """Run basic checks on ``file_obj`` using :class:`SecurityValidator`."""
        if file_obj is None:
            return ValidationResult(False, "No file provided")
        try:
            import pandas as pd

            if isinstance(file_obj, pd.DataFrame):
                size_mb = file_obj.memory_usage(deep=True).sum() / (1024 * 1024)
                if size_mb > self.max_size_mb:
                    return ValidationResult(
                        False,
                        f"Dataframe too large: {size_mb:.1f}MB > {self.max_size_mb}MB",
                    )
                return ValidationResult(True, "ok")
        except Exception:
            pass
        if isinstance(file_obj, (str, Path)):
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

        return ValidationResult(False, "Unsupported file type")

    def process_base64_contents(self, contents: str, filename: str) -> pd.DataFrame:
        """Decode ``contents`` and return a validated :class:`~pandas.DataFrame`."""
        if "," not in contents:
            raise FileValidationError("Invalid contents")
        _, data = contents.split(",", 1)
        file_bytes = base64.b64decode(data)
        self.validator.validate_file_upload(filename, file_bytes)
        df, err = process_file_simple(file_bytes, filename, config=self.config)
        if df is None:
            raise FileProcessingError(err or "Invalid file")
        return df


__all__ = [
    "FileHandler",
    "ValidationResult",
    "FileProcessingError",
    "process_file_simple",
]
