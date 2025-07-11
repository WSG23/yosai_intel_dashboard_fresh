"""Utility helpers for Yōsai Intel Dashboard."""

from core.unicode import (
    UnicodeProcessor,
    ChunkedUnicodeProcessor,
    UnicodeTextProcessor,
    UnicodeSQLProcessor,
    UnicodeSecurityProcessor,
    clean_unicode_text,
    sanitize_unicode_input,
    safe_decode_bytes,
    safe_encode_text,
    sanitize_dataframe,
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
from .protocols import SafeDecoderProtocol
from .debug_tools import (
    debug_callback_registration_flow,
    find_repeated_imports,
    print_registration_report,
)

__all__ = [
    "UnicodeProcessor",
    "ChunkedUnicodeProcessor",
    "UnicodeTextProcessor",
    "UnicodeSQLProcessor",
    "UnicodeSecurityProcessor",
    "clean_unicode_text",
    "sanitize_unicode_input",
    "safe_decode_bytes",
    "safe_encode_text",
    "sanitize_dataframe",
    "contains_surrogates",
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
    "SafeDecoderProtocol",
    "debug_callback_registration_flow",
    "find_repeated_imports",
    "print_registration_report",
]
