#!/usr/bin/env python3
from __future__ import annotations

"""File processing service - Core data processing without UI dependencies
Handles Unicode surrogate characters safely"""

import io
import logging
from typing import Any, Dict, Tuple


import pandas as pd

from yosai_intel_dashboard.src.infrastructure.config.constants import DEFAULT_CHUNK_SIZE
from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import dynamic_config
from core.performance import get_performance_monitor
from yosai_intel_dashboard.src.core.interfaces.protocols import ConfigurationProtocol

# Core processing imports only - NO UI COMPONENTS
from core.unicode import safe_format_number, safe_unicode_decode, sanitize_for_utf8
from yosai_intel_dashboard.src.services.data_processing.file_processor import (
    decode_contents,
    validate_metadata,
    dataframe_from_bytes,
)


logger = logging.getLogger(__name__)


class UnicodeFileProcessor:
    """Handle Unicode surrogate characters in file processing"""

    @staticmethod
    def safe_decode_content(content: bytes) -> str:
        return safe_decode_content(content)

    @staticmethod
    def sanitize_dataframe_unicode(
        df: pd.DataFrame,
        *,
        chunk_size: int | None = None,
        stream: bool = False,
    ) -> pd.DataFrame | Iterable[pd.DataFrame]:
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
                "error": "; ".join(info.get("issues", [])),
                "data": None,
                "filename": info.get("filename", filename),
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
    """Proxy for :func:`yosai_intel_dashboard.src.file_processing.create_file_preview`."""
    return _create_preview(df, max_rows=max_rows)


# For backwards compatibility expose ``UnicodeFileProcessor`` as ``FileProcessor``
FileProcessor = UnicodeFileProcessor

__all__ = [
    "UnicodeFileProcessor",
    "FileProcessor",
    "process_uploaded_file",
    "create_file_preview",
]
