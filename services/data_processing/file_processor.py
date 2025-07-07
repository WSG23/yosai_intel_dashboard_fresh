#!/usr/bin/env python3
"""
File processing service - Core data processing without UI dependencies
Handles Unicode surrogate characters safely
"""
import io
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import chardet
import pandas as pd

from config.config import get_analytics_config
from config.dynamic_config import dynamic_config
from core.performance import get_performance_monitor

# Core processing imports only - NO UI COMPONENTS
from core.unicode_utils import sanitize_for_utf8


def _get_max_display_rows() -> int:
    try:
        return get_analytics_config().max_display_rows or dynamic_config.analytics.max_display_rows
    except Exception:
        return dynamic_config.analytics.max_display_rows
from core.unicode_processor import safe_format_number
from services.analytics_service import MAX_DISPLAY_ROWS

logger = logging.getLogger(__name__)


class UnicodeFileProcessor:
    """Handle Unicode surrogate characters in file processing"""

    @staticmethod
    def safe_decode_content(content: bytes) -> str:
        """Safely decode file content handling Unicode surrogates"""
        try:
            # Detect encoding
            detected = chardet.detect(content)
            encoding = detected.get('encoding') or 'utf-8'

            from core.unicode_decode import safe_unicode_decode

            return safe_unicode_decode(content, encoding)
        except Exception as e:
            logger.warning(f"Unicode decode error: {e}")
            return safe_unicode_decode(content, "latin-1")

    @staticmethod
    def sanitize_dataframe_unicode(df: pd.DataFrame) -> pd.DataFrame:
        """Remove Unicode surrogate characters from DataFrame"""
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).apply(
                lambda x: sanitize_for_utf8(x) if isinstance(x, str) else x
            )
        return df

    def read_uploaded_file(
        self, contents: str, filename: str
    ) -> Tuple[pd.DataFrame, str | None]:
        """Process ``contents`` and return the DataFrame and error string."""
        result = process_uploaded_file(contents, filename)
        return result["data"], result["error"]

def process_uploaded_file(contents: str, filename: str) -> Dict[str, Any]:
    """
    Process uploaded file content safely
    Returns: Dict with 'data', 'filename', 'status', 'error'
    """
    try:
        # Decode base64 content
        import base64
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        # Safe Unicode processing
        text_content = UnicodeFileProcessor.safe_decode_content(decoded)

        chunk_size = getattr(dynamic_config.analytics, "chunk_size", 50000)
        monitor = get_performance_monitor()

        # Process based on file type
        if filename.endswith('.csv'):
            reader = pd.read_csv(io.StringIO(text_content), chunksize=chunk_size)
            chunks = []
            for chunk in reader:
                monitor.throttle_if_needed()
                chunks.append(chunk)
            df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return {
                'status': 'error',
                'error': f'Unsupported file type: {filename}',
                'data': None,
                'filename': filename
            }

        # Sanitize Unicode in DataFrame
        df = UnicodeFileProcessor.sanitize_dataframe_unicode(df)

        return {
            'status': 'success',
            'data': df,
            'filename': filename,
            'error': None
        }

    except Exception as e:
        logger.error(f"File processing error for {filename}: {e}")
        return {
            'status': 'error',
            'error': str(e),
            'data': None,
            'filename': filename
        }

def create_file_preview(df: pd.DataFrame, max_rows: int | None = None) -> Dict[str, Any]:
    """Create safe preview data without UI components"""
    try:
        limit = _get_max_display_rows()
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
            'preview_data': preview_data,
            'columns': list(df.columns),
            'total_rows': len(df),
            'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
    except Exception as e:
        logger.error(f"Preview creation error: {e}")
        return {
            'preview_data': [],
            'columns': [],
            'total_rows': 0,
            'dtypes': {}
        }

# For backwards compatibility expose ``UnicodeFileProcessor`` as ``FileProcessor``
FileProcessor = UnicodeFileProcessor

__all__ = [
    "UnicodeFileProcessor",
    "FileProcessor",
    "process_uploaded_file",
    "create_file_preview",
]

