"""Utility helpers for Yōsai Intel Dashboard with Unicode migration support."""

# Public helper used across the code base
try:
    from core.unicode_processor import process_large_csv_content
except Exception:  # pragma: no cover - fallback when dependencies fail
    process_large_csv_content = None  # type: ignore

try:  # pragma: no cover - graceful import fallback
    from core.unicode import (  # Preferred API; Deprecated API
        ChunkedUnicodeProcessor,
        UnicodeProcessor,
        clean_unicode_surrogates,
        clean_unicode_text,
        handle_surrogate_characters,
        safe_decode,
        safe_decode_bytes,
        safe_encode,
        safe_unicode_decode,
        safe_unicode_encode,
        sanitize_data_frame,
        sanitize_dataframe,
        sanitize_unicode_input,
    )

    # Migration aliases for transitional imports
    unicode_clean_text = clean_unicode_text
    unicode_safe_encode = safe_encode
    unicode_sanitize_df = sanitize_dataframe

    # Safe imports with fallbacks
    try:
        from .assets_debug import (
            check_navbar_assets,
            debug_dash_asset_serving,
            log_asset_info,
        )
    except ImportError:
        # Provide fallbacks when dash imports fail
        def check_navbar_assets(*args, **kwargs):
            return True

        def debug_dash_asset_serving(*args, **kwargs):
            return True

        def log_asset_info(*args, **kwargs):
            return None

    from .assets_utils import get_nav_icon
    from .preview_utils import serialize_dataframe_preview
    from .mapping_helpers import standardize_column_names, AIColumnMapperAdapter
except Exception:  # pragma: no cover - fallback when core.unicode unavailable
    from core.unicode_processor import safe_format_number
    from security.unicode_security_processor import (
        UnicodeSecurityProcessor,
    )
    from security.unicode_security_processor import (
        sanitize_dataframe as sanitize_data_frame,
    )
    from security.unicode_security_processor import (
        sanitize_unicode_input,
    )
    handle_surrogate_characters = UnicodeSecurityProcessor.sanitize_unicode_input
    clean_unicode_surrogates = UnicodeSecurityProcessor.sanitize_unicode_input
    unicode_clean_text = UnicodeSecurityProcessor.sanitize_unicode_input
    unicode_safe_encode = UnicodeSecurityProcessor.sanitize_unicode_input
    unicode_sanitize_df = sanitize_data_frame

    # Safe imports with fallbacks
    try:
        from .assets_debug import (
            check_navbar_assets,
            debug_dash_asset_serving,
            log_asset_info,
        )
    except ImportError:
        # Provide fallbacks when dash imports fail
        def check_navbar_assets(*args, **kwargs):
            return True

        def debug_dash_asset_serving(*args, **kwargs):
            return True

        def log_asset_info(*args, **kwargs):
            return None

    from .assets_utils import get_nav_icon
    from .preview_utils import serialize_dataframe_preview
    from .mapping_helpers import standardize_column_names, AIColumnMapperAdapter


__all__: list[str] = [
    # Preferred API
    "clean_unicode_text",
    "safe_decode_bytes",
    "safe_unicode_decode",
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
    "log_asset_info",
    "navbar_icon",
    "get_nav_icon",
    "serialize_dataframe_preview",
    "standardize_column_names",
    "AIColumnMapperAdapter",
]

