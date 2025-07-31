#!/usr/bin/env python3
"""
File processing service - Core data processing without UI dependencies
Handles Unicode surrogate characters safely
"""
from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import pandas as pd

from config.constants import DEFAULT_CHUNK_SIZE
from config.dynamic_config import dynamic_config
from core.performance import get_performance_monitor
from file_processing import create_file_preview as _create_preview
from file_processing import read_large_csv as _read_large_csv
from file_processing import (
    safe_decode_content,
    sanitize_dataframe_unicode,
)
from unicode_toolkit import safe_encode_text

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


def process_uploaded_file(
    contents: str,
    filename: str,
    *,
    config: Any = dynamic_config,
) -> Dict[str, Any]:
    """
    Process uploaded file content safely
    Returns: Dict with 'data', 'filename', 'status', 'error'
    """
    try:
        # Decode base64 content
        import base64

        if "," not in contents:
            return {
                "success": False,
                "error": "Invalid data URI",
                "data": None,
                "filename": filename,
            }

        _, content_string = contents.split(",", 1)
        decoded = base64.b64decode(content_string, validate=True)

        validator = SecurityValidator()
        meta = validator.validate_file_meta(filename, len(decoded))
        if not meta["valid"]:
            return {
                "success": False,
                "error": "; ".join(meta["issues"]),
                "data": None,
                "filename": filename,
            }
        filename = meta["filename"]

        # Safe Unicode processing
        text_content = UnicodeFileProcessor.safe_decode_content(decoded)

        chunk_size = getattr(config.analytics, "chunk_size", DEFAULT_CHUNK_SIZE)
        monitor = get_performance_monitor()

        # Process based on file type
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
            return {
                "success": False,
                "error": f"Unsupported file type: {filename}",
                "data": None,
                "filename": filename,
            }

        # Sanitize Unicode in DataFrame
        df = UnicodeFileProcessor.sanitize_dataframe_unicode(df)

        return {"success": True, "data": df, "filename": filename, "error": None}

    except Exception as e:
        logger.error(
            "File processing error for %s: %s",
            safe_encode_text(filename),
            e,
        )
        return {"success": False, "error": str(e), "data": None, "filename": filename}


def create_file_preview(
    df: pd.DataFrame, max_rows: int | None = None
) -> Dict[str, Any]:
    """Proxy for :func:`file_processing.create_file_preview`."""
    return _create_preview(df, max_rows=max_rows)


# For backwards compatibility expose ``UnicodeFileProcessor`` as ``FileProcessor``
FileProcessor = UnicodeFileProcessor

__all__ = [
    "UnicodeFileProcessor",
    "FileProcessor",
    "process_file_simple",
    "process_uploaded_file",
    "create_file_preview",
]
