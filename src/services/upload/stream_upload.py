"""Helpers for streaming file uploads."""
from __future__ import annotations

from typing import Any

from .unicode import normalize_text


def stream_upload(store, filename: str, data: Any) -> None:
    """Save ``data`` to ``store`` under a normalized ``filename``."""
    safe_name = normalize_text(filename)
    store.add_file(safe_name, data)
