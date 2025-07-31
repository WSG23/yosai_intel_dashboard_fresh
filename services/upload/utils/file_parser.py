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
from services.data_processing.file_processor import (
    decode_contents,
    validate_metadata,
    dataframe_from_bytes,
)

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
        decoded, decode_err = decode_contents(contents)
        if decoded is None:
            logger.error("Base64 decode failed for %s: %s", filename, decode_err)
            return {
                "status": "error",
                "error": decode_err,
                "data": None,
                "filename": filename,
            }

        sanitized, val_err = validate_metadata(filename, decoded)
        if sanitized is None:
            return {
                "status": "error",
                "error": val_err,
                "data": None,
                "filename": filename,
            }

        df, df_err = dataframe_from_bytes(decoded, sanitized, config=config)
        if df is None:
            return {
                "status": "error",
                "error": df_err,
                "data": None,
                "filename": sanitized,
            }

        return {"status": "success", "data": df, "filename": sanitized, "error": None}

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
