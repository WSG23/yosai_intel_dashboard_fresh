"""Utility helpers for Yōsai Intel Dashboard."""

from core.unicode import (
    ChunkedUnicodeProcessor,
    UnicodeProcessor,
    UnicodeTextProcessor,
    UnicodeSQLProcessor,
    UnicodeSecurityProcessor,
    clean_unicode_text,
    safe_decode_bytes,
    safe_encode_text,
    safe_unicode_decode,
    safe_decode,
    safe_encode,
    sanitize_dataframe,
    sanitize_data_frame,
    handle_surrogate_characters,
    clean_unicode_surrogates,
    sanitize_unicode_input,
    contains_surrogates,
    process_large_csv_content,
    safe_format_number,
    object_count,
)

from .assets_debug import (
    check_navbar_assets,
    debug_dash_asset_serving,
    log_asset_info,
)
from .assets_utils import get_nav_icon
from .preview_utils import serialize_dataframe_preview
from .mapping_helpers import standardize_column_names, AIColumnMapperAdapter

__all__ = [
    "clean_unicode_text",
    "safe_decode_bytes",
    "safe_encode_text",
    "safe_unicode_decode",
    "safe_decode",
    "safe_encode",
    "sanitize_dataframe",
    "sanitize_data_frame",
    "UnicodeProcessor",
    "ChunkedUnicodeProcessor",
    "UnicodeTextProcessor",
    "UnicodeSQLProcessor",
    "UnicodeSecurityProcessor",
    "contains_surrogates",
    "handle_surrogate_characters",
    "clean_unicode_surrogates",
    "sanitize_unicode_input",
    "process_large_csv_content",
    "safe_format_number",
    "object_count",
    "check_navbar_assets",
    "debug_dash_asset_serving",
    "log_asset_info",
    "get_nav_icon",
    "serialize_dataframe_preview",
    "standardize_column_names",
    "AIColumnMapperAdapter",
]
