"""Utility helpers for Yōsai Intel Dashboard."""

try:
    from .unicode_utils import safe_unicode_encode, handle_surrogate_characters
    from .unicode_processor import (
        sanitize_data_frame,
        clean_unicode_surrogates,
        sanitize_unicode_input,
        process_large_csv_content,
    )
except Exception:  # pragma: no cover - fallback when processor unavailable
    from .unicode_handler import sanitize_unicode_input, handle_surrogate_characters
    from .unicode_processor import safe_unicode_encode, sanitize_data_frame, clean_unicode_surrogates, process_large_csv_content  # type: ignore

__all__: list[str] = [
    "sanitize_unicode_input",
    "safe_unicode_encode",
    "handle_surrogate_characters",
    "sanitize_data_frame",
    "clean_unicode_surrogates",
    "process_large_csv_content",
]

