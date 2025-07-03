"""Utility helpers for Yōsai Intel Dashboard."""

try:
    from .unicode_utils import (
        safe_unicode_encode,
        handle_surrogate_characters,
        sanitize_unicode_input,
        sanitize_data_frame,
        clean_unicode_surrogates,
        process_large_csv_content,
        safe_format_number,
    )
    from .assets_debug import (
        check_navbar_assets,
        debug_dash_asset_serving,
        navbar_icon,
    )
    from .assets_utils import get_nav_icon
except Exception:  # pragma: no cover - fallback when utils unavailable
    from .unicode_utils import (
        safe_unicode_encode,
        handle_surrogate_characters,
        sanitize_unicode_input,
        sanitize_data_frame,
        clean_unicode_surrogates,
        process_large_csv_content,
        safe_format_number,
    )
    from .assets_debug import (
        check_navbar_assets,
        debug_dash_asset_serving,
        navbar_icon,
    )
    from .assets_utils import get_nav_icon

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
]
