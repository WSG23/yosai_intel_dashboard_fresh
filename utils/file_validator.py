"""
Simple file validation utilities
"""
import pandas as pd
import io
import base64
import binascii
import json
import logging
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)

from .unicode_handler import sanitize_unicode_input


def decode_bytes(data: bytes, enc: str) -> str:
    """Decode bytes using specified encoding with surrogatepass."""
    return data.decode(enc, errors="surrogatepass")


def safe_decode_with_unicode_handling(data: bytes, enc: str) -> str:
    """Decode with surrogatepass and clean to valid UTF-8."""
    try:
        text = data.decode(enc, errors="surrogatepass")
    except UnicodeDecodeError:
        text = data.decode(enc, errors="replace")

    text = sanitize_unicode_input(text)
    # Re-encode to UTF-8 ignoring any invalid surrogates/characters
    cleaned = text.encode("utf-8", errors="ignore")
    return cleaned.decode("utf-8", errors="ignore")


def validate_upload_content(contents: str, filename: str) -> Dict[str, Any]:
    """Validate uploaded file content"""

    # Basic validation
    if not contents or not filename:
        return {"valid": False, "error": "Missing file content or filename"}

    # Check if contents is properly formatted
    if not contents.startswith('data:'):
        return {"valid": False, "error": "Invalid file format - not a data URL"}

    if ',' not in contents:
        return {"valid": False, "error": "Invalid file format - missing data separator"}

    # Check file extension
    allowed_extensions = {'.csv', '.json', '.xlsx', '.xls'}
    file_ext = '.' + filename.split('.')[-1].lower() if '.' in filename else ''

    if file_ext not in allowed_extensions:
        return {
            "valid": False,
            "error": f"File type {file_ext} not supported. Allowed: {', '.join(allowed_extensions)}"
        }

    return {"valid": True, "extension": file_ext}


def safe_decode_file(contents: str) -> Optional[bytes]:
    """Safely decode base64 file contents"""
    try:
        # Split the data URL
        if ',' not in contents:
            return None

        content_type, content_string = contents.split(',', 1)

        # Decode base64
        decoded = base64.b64decode(content_string)
        return decoded

    except (binascii.Error, ValueError):
        return None
    except Exception as e:  # pragma: no cover - unexpected
        logger.exception("Unexpected error decoding file", exc_info=e)
        raise


def process_dataframe(decoded: bytes, filename: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    """Process decoded bytes into DataFrame"""
    try:
        filename_lower = filename.lower()

        if filename_lower.endswith('.csv'):
            # Try multiple encodings with surrogate handling
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    text = safe_decode_with_unicode_handling(decoded, encoding)
                    df = pd.read_csv(io.StringIO(text))
                    return df, None
                except UnicodeDecodeError:
                    continue
            return None, "Could not decode CSV with any standard encoding"

        elif filename_lower.endswith('.json'):
            import json
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    text = safe_decode_with_unicode_handling(decoded, encoding)
                    json_data = json.loads(text)
                    if isinstance(json_data, list):
                        df = pd.DataFrame(json_data)
                    else:
                        df = pd.DataFrame([json_data])
                    return df, None
                except UnicodeDecodeError:
                    continue
            return None, "Could not decode JSON with any standard encoding"

        elif filename_lower.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(decoded))
            return df, None

        else:
            return None, f"Unsupported file type: {filename}"

    except (
        UnicodeDecodeError,
        ValueError,
        pd.errors.ParserError,
        json.JSONDecodeError,
    ) as e:
        return None, f"Error processing file: {str(e)}"
    except Exception as e:  # pragma: no cover - unexpected
        logger.exception("Unexpected error processing file", exc_info=e)
        raise
