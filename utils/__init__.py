"""Utility helpers for Yōsai Intel Dashboard with Unicode migration support."""

# Public helper used across the code base
try:
    from core.unicode_processor import process_large_csv_content
except Exception:  # pragma: no cover - fallback when dependencies fail
    process_large_csv_content = None  # type: ignore

try:  # pragma: no cover - graceful import fallback
    from .unicode_utils import (
        # Preferred API
        clean_unicode_text,
        safe_decode_bytes,
        safe_encode,
        sanitize_dataframe,
        UnicodeProcessor,
        ChunkedUnicodeProcessor,
        # Deprecated API
        safe_unicode_encode,
        safe_encode,
        safe_decode,
        handle_surrogate_characters,
        clean_unicode_surrogates,
        sanitize_unicode_input,
        sanitize_data_frame,
    )

    # Migration aliases for transitional imports
    unicode_clean_text = clean_unicode_text
    unicode_safe_encode = safe_encode
    unicode_sanitize_df = sanitize_dataframe

    from .assets_debug import (
        check_navbar_assets,
        debug_dash_asset_serving,
        navbar_icon,
    )
    from .assets_utils import get_nav_icon
    from .preview_utils import serialize_dataframe_preview
except Exception:  # pragma: no cover - fallback when unicode_utils unavailable
    from security.unicode_security_processor import (
        sanitize_dataframe as sanitize_data_frame,
        UnicodeSecurityProcessor,
        sanitize_unicode_input,
    )
    from core.unicode_processor import safe_format_number
    handle_surrogate_characters = UnicodeSecurityProcessor.sanitize_unicode_input
    clean_unicode_surrogates = UnicodeSecurityProcessor.sanitize_unicode_input
    unicode_clean_text = UnicodeSecurityProcessor.sanitize_unicode_input
    unicode_safe_encode = UnicodeSecurityProcessor.sanitize_unicode_input
    unicode_sanitize_df = sanitize_data_frame

    from .assets_debug import (
        check_navbar_assets,
        debug_dash_asset_serving,
        navbar_icon,
    )
    from .assets_utils import get_nav_icon
    from .preview_utils import serialize_dataframe_preview


__all__: list[str] = [
    # Preferred API
    "clean_unicode_text",
    "safe_decode_bytes",
    "safe_encode",
    "sanitize_dataframe",
    "UnicodeProcessor",
    "ChunkedUnicodeProcessor",
    # Migration aliases
    "unicode_clean_text",
    "unicode_safe_encode",
    "unicode_sanitize_df",
    # Deprecated API
    "safe_unicode_encode",
    "safe_encode",
    "safe_decode",
    "handle_surrogate_characters",
    "clean_unicode_surrogates",
    "sanitize_unicode_input",
    "sanitize_data_frame",
    "process_large_csv_content",
    # Existing utilities
    "check_navbar_assets",
    "debug_dash_asset_serving",
    "navbar_icon",
    "get_nav_icon",
    "serialize_dataframe_preview",
]

