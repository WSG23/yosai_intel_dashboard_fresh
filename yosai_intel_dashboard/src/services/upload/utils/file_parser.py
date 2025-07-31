#!/usr/bin/env python3
"""
File processing service - Core data processing without UI dependencies
Handles Unicode surrogate characters safely
"""
import io
import json
import logging
from unicode_toolkit import safe_encode_text
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import chardet
import pandas as pd

from config.constants import DEFAULT_CHUNK_SIZE
from config.dynamic_config import dynamic_config
from core.config import get_max_display_rows
from core.performance import get_performance_monitor
from core.protocols import ConfigurationProtocol

# Core processing imports only - NO UI COMPONENTS
from core.unicode import safe_format_number, safe_unicode_decode, sanitize_for_utf8

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
    def sanitize_dataframe_unicode(df: pd.DataFrame) -> pd.DataFrame:
        """Remove Unicode surrogate characters from DataFrame"""
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = (
                df[col]
                .astype(str)
                .apply(lambda x: sanitize_for_utf8(x) if isinstance(x, str) else x)
            )
        return df

    def read_uploaded_file(
        self, contents: str, filename: str
    ) -> Tuple[pd.DataFrame, str | None]:
        """Process ``contents`` and return the DataFrame and error string."""
        result = process_uploaded_file(contents, filename)
        return result["data"], result["error"]


def _safe_b64decode(contents: str) -> Tuple[Optional[bytes], Optional[str]]:
    """Return decoded bytes or an error message."""
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


def process_uploaded_file(
    contents: str,
    filename: str,
    *,
    config: ConfigurationProtocol = dynamic_config,
) -> Dict[str, Any]:
    """
    Process uploaded file content safely
    Returns: Dict with 'data', 'filename', 'status', 'error'
    """
    try:
        decoded, decode_err = _safe_b64decode(contents)
        if decoded is None:
            logger.error("Base64 decode failed for %s: %s", filename, decode_err)
            return {
                "status": "error",
                "error": decode_err,
                "data": None,
                "filename": filename,
            }
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
                "status": "error",
                "error": f"Unsupported file type: {filename}",
                "data": None,
                "filename": filename,
            }

        # Sanitize Unicode in DataFrame
        df = UnicodeFileProcessor.sanitize_dataframe_unicode(df)

        return {"status": "success", "data": df, "filename": filename, "error": None}

    except Exception as e:
        logger.error(
            "File processing error for %s: %s",
            safe_encode_text(filename),
            e,
        )
        return {"status": "error", "error": str(e), "data": None, "filename": filename}


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
                    safe_row[col] = sanitize_for_utf8(str(val))
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
    "process_uploaded_file",
    "create_file_preview",
]
