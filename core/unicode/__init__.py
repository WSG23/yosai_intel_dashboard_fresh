from ..unicode_processor import *
from ..unicode_processor import safe_decode_bytes, safe_encode_text
from ..unicode_decode import safe_unicode_decode
from typing import Any, Dict, Iterable
from .processor import (
    UnicodeSecurityProcessor,
    UnicodeSQLProcessor,
    UnicodeTextProcessor,
)


def object_count(items: Iterable[Any]) -> int:
    """Return the number of unique strings appearing more than once."""

    counts: Dict[str, int] = {}
    for item in items:
        if isinstance(item, str):
            counts[item] = counts.get(item, 0) + 1

    return sum(1 for v in counts.values() if v > 1)

__all__ = [
    "UnicodeProcessor",
    "ChunkedUnicodeProcessor",
    "clean_unicode_text",
    "safe_decode_bytes",
    "safe_encode_text",
    "safe_unicode_decode",
    "safe_decode",
    "safe_encode",
    "sanitize_dataframe",
    "sanitize_data_frame",
    "handle_surrogate_characters",
    "clean_unicode_surrogates",
    "sanitize_unicode_input",
    "contains_surrogates",
    "process_large_csv_content",
    "safe_format_number",
    "object_count",
    "UnicodeTextProcessor",
    "UnicodeSQLProcessor",
    "UnicodeSecurityProcessor",
]
