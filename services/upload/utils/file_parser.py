#!/usr/bin/env python3
from __future__ import annotations

"""File processing service - Core data processing without UI dependencies
Handles Unicode surrogate characters safely"""

import io
import logging
from typing import Any, Dict, Tuple


import pandas as pd

from config.constants import DEFAULT_CHUNK_SIZE
from config.dynamic_config import dynamic_config
from core.performance import get_performance_monitor
from core.protocols import ConfigurationProtocol

# Core processing imports only - NO UI COMPONENTS
from core.unicode import safe_format_number, safe_unicode_decode, sanitize_for_utf8
from unicode_toolkit import safe_encode_text
from validation.security_validator import SecurityValidator
from validation.upload_utils import decode_and_validate_upload


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
        validator = SecurityValidator()
        info = decode_and_validate_upload(contents, filename, validator)
        if not info["valid"]:
            logger.error(
                "Base64 validation failed for %s: %s",
                filename,
                ", ".join(info.get("issues", [])),
            )
            return {
                "status": "error",
                "error": "; ".join(info.get("issues", [])),
                "data": None,
                "filename": info.get("filename", filename),
            }
        decoded = info["decoded"]
        filename = info["filename"]
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
    """Proxy for :func:`file_processing.create_file_preview`."""
    return _create_preview(df, max_rows=max_rows)


# For backwards compatibility expose ``UnicodeFileProcessor`` as ``FileProcessor``
FileProcessor = UnicodeFileProcessor

__all__ = [
    "UnicodeFileProcessor",
    "FileProcessor",
    "process_uploaded_file",
    "create_file_preview",
]
