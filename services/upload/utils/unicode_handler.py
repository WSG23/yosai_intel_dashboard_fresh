"""Utility functions for safe Unicode handling in uploads."""
from __future__ import annotations

import base64
import logging
from typing import Union, Tuple

from core.unicode_processor import safe_encode_text

logger = logging.getLogger(__name__)


def safe_unicode_encode(text: Union[str, bytes, None]) -> str:
    """Deprecated alias for :func:`safe_encode_text`."""

    return safe_encode_text(text)


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
    return decoded, safe_encode_text(filename)


__all__ = ["safe_unicode_encode", "decode_upload_content"]
