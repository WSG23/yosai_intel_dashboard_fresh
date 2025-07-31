#!/usr/bin/env python3
"""
File processing service - Core data processing without UI dependencies
Handles Unicode surrogate characters safely
"""
import io
import logging
from pathlib import Path
from typing import Any, Dict, Iterable, Tuple

import chardet
import pandas as pd

from config.constants import DEFAULT_CHUNK_SIZE
from config.dynamic_config import dynamic_config
from core.config import get_max_display_rows
from core.performance import get_performance_monitor
from core.performance_file_processor import PerformanceFileProcessor
from core.unicode import UnicodeProcessor as UnicodeHelper
from core.unicode import safe_format_number, safe_unicode_decode
from unicode_toolkit import safe_encode_text
from validation.security_validator import SecurityValidator

from .file_handler import process_file_simple

# Core processing imports only - NO UI COMPONENTS


logger = logging.getLogger(__name__)


class UnicodeFileProcessor:
    """Handle Unicode surrogate characters in file processing"""

    @staticmethod
    def safe_decode_content(content: bytes) -> str:
        """Safely decode file content handling Unicode surrogates"""
        try:
            # Detect encoding
            detected = chardet.detect(content)
            encoding = detected.get("encoding") or "utf-8"

            return safe_unicode_decode(content, encoding)
        except Exception as e:
            logger.warning(f"Unicode decode error: {e}")
            return safe_unicode_decode(content, "latin-1")

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

        if chunk_size is None:
            chunk_size = getattr(
                dynamic_config.analytics, "chunk_size", DEFAULT_CHUNK_SIZE
            )

        processor = PerformanceFileProcessor(
            chunk_size=chunk_size, max_memory_mb=max_memory_mb
        )
        return processor.process_large_csv(file_path, encoding=encoding, stream=stream)

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

        if chunk_size is None:
            chunk_size = getattr(
                dynamic_config.analytics, "chunk_size", DEFAULT_CHUNK_SIZE
            )

        obj_cols = list(df.select_dtypes(include=["object"]).columns)

        if not obj_cols:
            if stream:

                def _gen() -> Iterable[pd.DataFrame]:
                    for start in range(0, len(df), chunk_size):
                        yield df.iloc[start : start + chunk_size]

                return _gen()
            return df

        def _generator() -> Iterable[pd.DataFrame]:
            for start in range(0, len(df), chunk_size):
                chunk = df.iloc[start : start + chunk_size].copy()
                for col in obj_cols:
                    chunk[col] = [
                        UnicodeHelper.clean_text(x) if isinstance(x, str) else x
                        for x in chunk[col].astype(str)
                    ]
                yield chunk

        if stream:
            return _generator()

        cleaned_chunks = list(_generator())
        return (
            pd.concat(cleaned_chunks, ignore_index=True)
            if cleaned_chunks
            else pd.DataFrame()
        )

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
    meta = validator.validate_file_meta(filename, len(decoded))
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
                "filename": filename,
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
    """Create safe preview data without UI components"""
    try:
        limit = get_max_display_rows()
        rows = min(max_rows if max_rows is not None else limit, limit)
        preview_df = df.head(rows)

        # Ensure all data is JSON serializable and Unicode-safe
        preview_data = []
        for _, row in preview_df.iterrows():
            safe_row = {}
            for col, val in row.items():
                if pd.isna(val):
                    safe_row[col] = None
                elif isinstance(val, (int, float)):
                    safe_row[col] = safe_format_number(val)
                else:
                    safe_row[col] = UnicodeHelper.clean_text(str(val))
            preview_data.append(safe_row)

        return {
            "preview_data": preview_data,
            "columns": list(df.columns),
            "total_rows": len(df),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        }
    except Exception as e:
        logger.error(f"Preview creation error: {e}")
        return {"preview_data": [], "columns": [], "total_rows": 0, "dtypes": {}}


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
