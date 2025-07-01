#!/usr/bin/env python3
"""Unicode surrogate character handler for UTF-8 encoding safety."""

import unicodedata
from typing import Union, Any


def sanitize_unicode_input(text: Union[str, Any], replacement: str = '?') -> str:
    """
    Sanitize text input to handle Unicode surrogate characters.
    
    Args:
        text: Input text or any object that can be converted to string
        replacement: Character to replace problematic Unicode with
        
    Returns:
        Safe UTF-8 encoded string
    """
    if text is None:
        return ''
    
    if not isinstance(text, str):
        text = str(text)

    try:
        cleaned = text.encode('utf-8', errors='ignore').decode('utf-8')
        cleaned = unicodedata.normalize('NFKC', cleaned)
        cleaned = ''.join(
            char for char in cleaned
            if unicodedata.category(char)[0] != 'C' or char in '\t\n\r'
        )
        return cleaned
    except (UnicodeError, UnicodeDecodeError, UnicodeEncodeError):
        return ''.join(char for char in str(text) if ord(char) < 127)


def safe_format_number(value: Union[int, float], default: str = '0') -> str:
    """Safely format numbers with Unicode safety."""
    try:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return f"{value:,}"
        return default
    except (ValueError, TypeError):
        return default
