"""Utility functions for safe Unicode handling in uploads."""
from __future__ import annotations

import base64
import logging
from typing import Union, Tuple

logger = logging.getLogger(__name__)


def safe_unicode_encode(text: Union[str, bytes, None]) -> str:
    """Safely encode text to UTF-8, replacing problematic characters."""
    if text is None:
        return ""
    if isinstance(text, bytes):
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                text = text.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            text = text.decode("utf-8", errors="replace")
    if isinstance(text, str):
        try:
            text.encode("utf-8")
            return text
        except UnicodeEncodeError:
            return text.encode("utf-8", errors="replace").decode("utf-8")
    return str(text)


def decode_upload_content(content: str, filename: str) -> Tuple[bytes, str]:
    """Decode base64 upload content and return bytes and safe filename."""
    if not content:
        raise ValueError("No content provided")
    if "," in content:
        _, content = content.split(",", 1)
    try:
        decoded = base64.b64decode(content)
    except Exception as exc:
        logger.error("Failed to decode upload content: %s", exc)
        raise ValueError(f"Invalid file content: {exc}")
    return decoded, safe_unicode_encode(filename)


__all__ = ["safe_unicode_encode", "decode_upload_content"]
