from __future__ import annotations

"""File I/O helpers applying :class:`UnicodeHandler` sanitization."""

import json
import logging
from pathlib import Path
from typing import Any

from unicode_toolkit import safe_encode_text
from .unicode_handler import UnicodeHandler

logger = logging.getLogger(__name__)


def read_text(path: Path) -> str:
    """Read text from ``path`` and sanitize the result."""
    data = path.read_text(encoding="utf-8")
    cleaned = UnicodeHandler.sanitize(data)
    logger.info("Sanitized read from %s", UnicodeHandler.sanitize(str(path)))
    return cleaned


def write_text(path: Path, data: str) -> None:
    """Sanitize ``data`` and write it to ``path``."""
    cleaned = UnicodeHandler.sanitize(data)
    path.write_text(cleaned, encoding="utf-8")
    logger.info("Sanitized write to %s", UnicodeHandler.sanitize(str(path)))

def read_json(path: Path) -> Any:
    """Read JSON from ``path`` applying sanitization."""
    text = read_text(path)
    return json.loads(text)


def write_json(path: Path, data: Any) -> None:
    """Serialize ``data`` as JSON after sanitizing."""
    cleaned = UnicodeHandler.sanitize(data)
    path.write_text(
        json.dumps(cleaned, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    logger.info("Sanitized write to %s", UnicodeHandler.sanitize(str(path)))

__all__ = ["read_text", "write_text", "read_json", "write_json"]
