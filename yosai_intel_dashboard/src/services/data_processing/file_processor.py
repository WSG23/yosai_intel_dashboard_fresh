#!/usr/bin/env python3
from __future__ import annotations

"""File processing service - Core data processing without UI dependencies
Handles Unicode surrogate characters safely"""

import io
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import pandas as pd

from yosai_intel_dashboard.src.infrastructure.config.constants import DEFAULT_CHUNK_SIZE
from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import dynamic_config
from yosai_intel_dashboard.src.core.performance import get_performance_monitor
from yosai_intel_dashboard.src.file_processing import (
    create_file_preview as _create_preview,
    read_large_csv as _read_large_csv,
    safe_decode_content,
    sanitize_dataframe_unicode,
)
from unicode_toolkit import safe_encode_text
from validation.security_validator import SecurityValidator
from yosai_intel_dashboard.src.core.exceptions import ValidationError


from .file_handler import process_file_simple

# Core processing imports only - NO UI COMPONENTS


logger = logging.getLogger(__name__)


class UnicodeFileProcessor:
    """Handle Unicode surrogate characters in file processing"""

    @staticmethod
    def safe_decode_content(content: bytes) -> str:
        return safe_decode_content(content)

    @staticmethod
    def read_large_csv(
        file_path: str | Path | io.TextIOBase,
        *,
        encoding: str = "utf-8",
        chunk_size: int | None = None,
        max_memory_mb: int | None = None,
        stream: bool = False,
    ) -> pd.DataFrame | Iterable[pd.DataFrame]:
        """Load a potentially huge CSV file via :class:`PerformanceFileProcessor`."""

        return _read_large_csv(
            file_path,
            encoding=encoding,
            chunk_size=chunk_size,
            max_memory_mb=max_memory_mb,
            stream=stream,
        )

    @staticmethod
    def sanitize_dataframe_unicode(
        df: pd.DataFrame,
        *,
        chunk_size: int | None = None,
        stream: bool = False,
    ) -> pd.DataFrame | Iterable[pd.DataFrame]:
        """Return ``df`` sanitized for UTF-8 text.

        When ``stream`` is ``True`` a generator yielding cleaned DataFrame
        chunks is returned. This avoids loading the entire DataFrame into
        memory at once and mirrors :func:`process_large_content`.
        """

        return sanitize_dataframe_unicode(df, chunk_size=chunk_size, stream=stream)

    def read_uploaded_file(
        self, contents: str, filename: str
    ) -> Tuple[pd.DataFrame, str | None]:
        """Process ``contents`` and return the DataFrame and error string."""
        result = process_uploaded_file(contents, filename)
        return result["data"], result["error"]


def decode_contents(contents: str) -> Tuple[bytes | None, str | None]:
    """Decode a base64 data URI."""
    import base64

    if "," not in contents:
        return None, "Invalid data URI"
    try:
        _, content_string = contents.split(",", 1)
        decoded = base64.b64decode(content_string, validate=True)
        if not decoded:
            return None, "Empty file contents"
        return decoded, None
    except (base64.binascii.Error, ValueError) as exc:
        return None, f"Invalid base64 data: {exc}"


def validate_metadata(filename: str, decoded: bytes) -> Tuple[str | None, str | None]:
    """Validate filename and size using :class:`SecurityValidator`."""
    validator = SecurityValidator()
    try:
        meta = validator.validate_file_meta(filename, decoded)
    except ValidationError as exc:
        return None, str(exc)
    if not meta["valid"]:
        return None, "; ".join(meta["issues"])
    return meta["filename"], None


def dataframe_from_bytes(
    decoded: bytes, filename: str, *, config: Any = dynamic_config
) -> Tuple[pd.DataFrame | None, str | None]:
    """Create a DataFrame from ``decoded`` bytes based on ``filename``."""
    text_content = UnicodeFileProcessor.safe_decode_content(decoded)
    chunk_size = getattr(config.analytics, "chunk_size", DEFAULT_CHUNK_SIZE)
    monitor = get_performance_monitor()

    if filename.endswith(".csv"):
        reader = pd.read_csv(io.StringIO(text_content), chunksize=chunk_size)
        chunks = []
        for chunk in reader:
            monitor.throttle_if_needed()
            chunks.append(chunk)
        df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
    elif filename.endswith((".xlsx", ".xls")):
        df = pd.read_excel(io.BytesIO(decoded))
    else:
        return None, f"Unsupported file type: {filename}"

    df = UnicodeFileProcessor.sanitize_dataframe_unicode(df)
    return df, None


def process_uploaded_file(
    contents: str,
    filename: str,
    *,
    config: Any = dynamic_config,
) -> Dict[str, Any]:
    """Process uploaded file content safely."""
    try:
        decoded, err = decode_contents(contents)
        if decoded is None:
            logger.error("Base64 decode failed for %s: %s", filename, err)
            return {
                "success": False,
                "error": err,
                "data": None,
                "filename": filename,
            }

        sanitized, err = validate_metadata(filename, decoded)
        if sanitized is None:
            return {
                "success": False,
                "error": err,

                "data": None,
                "filename": info.get("filename", filename),
            }

        df, err = dataframe_from_bytes(decoded, sanitized, config=config)
        if df is None:

            return {
                "success": False,
                "error": err,
                "data": None,
                "filename": sanitized,
            }

        return {"success": True, "data": df, "filename": sanitized, "error": None}

    except Exception as e:  # pragma: no cover - best effort
        logger.error("File processing error for %s: %s", safe_encode_text(filename), e)
        return {"success": False, "error": str(e), "data": None, "filename": filename}


def create_file_preview(
    df: pd.DataFrame, max_rows: int | None = None
) -> Dict[str, Any]:
    """Proxy for :func:`yosai_intel_dashboard.src.file_processing.create_file_preview`."""
    return _create_preview(df, max_rows=max_rows)


# For backwards compatibility expose ``UnicodeFileProcessor`` as ``FileProcessor``
FileProcessor = UnicodeFileProcessor

__all__ = [
    "UnicodeFileProcessor",
    "FileProcessor",
    "process_file_simple",
    "decode_contents",
    "validate_metadata",
    "dataframe_from_bytes",
    "process_uploaded_file",
    "create_file_preview",
]
