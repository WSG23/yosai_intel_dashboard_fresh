#!/usr/bin/env python3
"""
File processing service - Core data processing without UI dependencies
Handles Unicode surrogate characters safely
"""
import logging
import pandas as pd
import json
import io
import chardet
from typing import Optional, Dict, Any, List, Tuple, Union
from pathlib import Path

# Core processing imports only - NO UI COMPONENTS
from security.unicode_security_processor import sanitize_unicode_input
from core.unicode_processor import safe_format_number

logger = logging.getLogger(__name__)


class UnicodeFileProcessor:
    """Handle Unicode surrogate characters in file processing"""

    @staticmethod
    def safe_decode_content(content: bytes) -> str:
        """Safely decode file content handling Unicode surrogates"""
        try:
            # Detect encoding
            detected = chardet.detect(content)
            encoding = detected.get('encoding', 'utf-8')

            # Try detected encoding first
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                # Fallback to utf-8 with error handling
                return content.decode('utf-8', errors='replace')
        except Exception as e:
            logger.warning(f"Unicode decode error: {e}")
            # Last resort: latin-1 can decode any byte sequence
            return content.decode('latin-1')

    @staticmethod
    def sanitize_dataframe_unicode(df: pd.DataFrame) -> pd.DataFrame:
        """Remove Unicode surrogate characters from DataFrame"""
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).apply(
                lambda x: sanitize_unicode_input(x) if isinstance(x, str) else x
            )
        return df

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

        # Process based on file type
        if filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(text_content))
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

def create_file_preview(df: pd.DataFrame, max_rows: int = 10) -> Dict[str, Any]:
    """Create safe preview data without UI components"""
    try:
        preview_df = df.head(max_rows)
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
                    safe_row[col] = sanitize_unicode_input(str(val))
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

