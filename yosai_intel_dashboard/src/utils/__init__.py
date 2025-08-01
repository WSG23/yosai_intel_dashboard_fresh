"""Utility helpers for Yōsai Intel Dashboard."""

from yosai_intel_dashboard.src.core.unicode import (
    ChunkedUnicodeProcessor,
    EnhancedUnicodeProcessor,
    SurrogateHandlingConfig,
    SurrogateHandlingStrategy,
    UnicodeProcessor,
    UnicodeSecurityProcessor,
    UnicodeSQLProcessor,
    UnicodeTextProcessor,
    clean_unicode_text,
    contains_surrogates,
    object_count,
    process_large_csv_content,
    safe_decode_bytes,
    safe_encode_text,
    safe_format_number,
    sanitize_dataframe,
    sanitize_unicode_input,
    secure_unicode_sanitization,
    utf8_safe_decode,
    utf8_safe_encode,
)
from mapping.processors.ai_processor import AIColumnMapperAdapter

from .assets_debug import (
    check_navbar_assets,
    debug_dash_asset_serving,
    log_asset_info,
)
from .assets_utils import get_nav_icon
from .config_resolvers import (
    resolve_ai_confidence_threshold,
    resolve_max_upload_size_mb,
    resolve_upload_chunk_size,
)
from .debug_tools import (
    debug_callback_registration_flow,
    find_repeated_imports,
    print_registration_report,
)
from .file_utils import safe_decode_with_unicode_handling
from .hashing import hash_dataframe
from .io_helpers import read_json, read_text, write_json, write_text
from .mapping_helpers import standardize_column_names
from .preview_utils import serialize_dataframe_preview
from .protocols import SafeDecoderProtocol
from .unicode_handler import UnicodeHandler

__all__ = [
    "UnicodeProcessor",
    "ChunkedUnicodeProcessor",
    "UnicodeTextProcessor",
    "UnicodeSQLProcessor",
    "UnicodeSecurityProcessor",
    "EnhancedUnicodeProcessor",
    "SurrogateHandlingConfig",
    "SurrogateHandlingStrategy",
    "clean_unicode_text",
    "sanitize_unicode_input",
    "safe_decode_bytes",
    "safe_decode_with_unicode_handling",
    "safe_encode_text",
    "sanitize_dataframe",
    "contains_surrogates",
    "secure_unicode_sanitization",
    "utf8_safe_encode",
    "utf8_safe_decode",
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
    "UnicodeHandler",
    "read_json",
    "write_json",
    "read_text",
    "write_text",
    "hash_dataframe",
    "resolve_ai_confidence_threshold",
    "resolve_max_upload_size_mb",
    "resolve_upload_chunk_size",
]
