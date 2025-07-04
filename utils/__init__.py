"""Utility helpers for Yōsai Intel Dashboard."""

try:
    from unicode_handler import (
        safe_encode as safe_unicode_encode,
        UnicodeProcessor,
        sanitize_dataframe as sanitize_data_frame,
    )
    handle_surrogate_characters = UnicodeProcessor.clean_surrogate_chars
    sanitize_unicode_input = UnicodeProcessor.safe_encode_text
    clean_unicode_surrogates = UnicodeProcessor.clean_surrogate_chars
    from unicode_handler import process_large_csv_content, safe_format_number
    from .assets_debug import (
        check_navbar_assets,
        debug_dash_asset_serving,
        navbar_icon,
    )
    from .assets_utils import get_nav_icon
    from .preview_utils import serialize_dataframe_preview
except Exception:  # pragma: no cover - fallback when utils unavailable
    from unicode_handler import (
        safe_encode as safe_unicode_encode,
        UnicodeProcessor,
        sanitize_dataframe as sanitize_data_frame,
        process_large_csv_content,
        safe_format_number,
    )
    handle_surrogate_characters = UnicodeProcessor.clean_surrogate_chars
    sanitize_unicode_input = UnicodeProcessor.safe_encode_text
    clean_unicode_surrogates = UnicodeProcessor.clean_surrogate_chars
    from .assets_debug import (
        check_navbar_assets,
        debug_dash_asset_serving,
        navbar_icon,
    )
    from .assets_utils import get_nav_icon
    from .preview_utils import serialize_dataframe_preview

__all__: list[str] = [
    "sanitize_unicode_input",
    "safe_unicode_encode",
    "handle_surrogate_characters",
    "sanitize_data_frame",
    "clean_unicode_surrogates",
    "process_large_csv_content",
    "safe_format_number",
    "check_navbar_assets",
    "debug_dash_asset_serving",
    "navbar_icon",
    "get_nav_icon",
    "serialize_dataframe_preview",
]
