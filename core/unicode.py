#!/usr/bin/env python3
"""
Unicode handling module with surrogate character protection.
Replace existing core/unicode.py entirely.
"""

import logging
import re
import unicodedata
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Unicode surrogate pair range
SURROGATE_PATTERN = re.compile(r'[\uD800-\uDFFF]')


def safe_encode_text(text: Any, fallback: str = "?") -> str:
    """
    Safely encode text handling Unicode surrogate characters.
    
    Args:
        text: Input text (any type will be converted to string)
        fallback: Character to use when encoding fails
        
    Returns:
        UTF-8 safe string without surrogate characters
    """
    if text is None:
        return ""
    
    try:
        # Convert to string first
        text_str = str(text)
        
        # Remove surrogate characters that can't be encoded in UTF-8
        text_str = SURROGATE_PATTERN.sub(fallback, text_str)
        
        # Normalize Unicode to handle any combining characters
        text_str = unicodedata.normalize('NFKC', text_str)
        
        # Test encoding to catch any remaining issues
        text_str.encode('utf-8')
        
        return text_str
        
    except (UnicodeEncodeError, UnicodeDecodeError) as e:
        logger.warning(f"Unicode encoding failed for '{text}': {e}")
        # Fall back to ASCII with ignore
        try:
            return str(text).encode('ascii', 'ignore').decode('ascii')
        except Exception:
            return fallback
    
    except Exception as e:
        logger.error(f"Unexpected error in safe_encode_text: {e}")
        return fallback


def safe_decode_bytes(data: bytes, encoding: str = 'utf-8') -> str:
    """
    Safely decode bytes to string with error handling.
    
    Args:
        data: Bytes to decode
        encoding: Target encoding (default: utf-8)
        
    Returns:
        Decoded string
    """
    try:
        decoded = data.decode(encoding, errors='replace')
        return safe_encode_text(decoded)
    except Exception as e:
        logger.error(f"Byte decoding failed: {e}")
        return data.decode('ascii', errors='ignore')


def clean_filename(filename: str) -> str:
    """
    Clean filename for safe filesystem use.
    
    Args:
        filename: Input filename
        
    Returns:
        Clean filename safe for filesystem
    """
    if not filename:
        return "untitled"
    
    # Remove problematic characters
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', filename)
    cleaned = safe_encode_text(cleaned, '_')
    
    # Truncate if too long
    if len(cleaned) > 255:
        name, ext = cleaned.rsplit('.', 1) if '.' in cleaned else (cleaned, '')
        cleaned = f"{name[:250]}.{ext}" if ext else cleaned[:255]
    
    return cleaned or "untitled"


def truncate_safe(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Safely truncate text without breaking Unicode.
    
    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    safe_text = safe_encode_text(text)
    
    if len(safe_text) <= max_length:
        return safe_text
    
    truncated = safe_text[:max_length - len(suffix)]
    return f"{truncated}{suffix}"


__all__ = [
    "safe_encode_text",
    "safe_decode_bytes", 
    "clean_filename",
    "truncate_safe"
]
