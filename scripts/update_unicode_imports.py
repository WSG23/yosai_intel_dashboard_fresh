"""Guide to update legacy Unicode utilities to the new API.

This script prints mappings of old function names to the new preferred
replacements.  It does not modify any files.  Use the output to update the
codebase manually or with your own tooling.
"""

from __future__ import annotations

import re

REPLACEMENTS = {
    "safe_unicode_encode": "safe_encode_text",
    "safe_encode": "safe_encode_text",
    "safe_decode": "safe_decode_bytes",
    "sanitize_unicode_input": "safe_encode_text",
    "sanitize_data_frame": "sanitize_dataframe",
}

METHOD_PATTERNS = {
    r"UnicodeProcessor\.clean_surrogate_chars": "UnicodeProcessor.clean_text",
    r"UnicodeProcessor\.safe_encode_text": "UnicodeProcessor.safe_encode",
    r"UnicodeProcessor\.safe_decode_bytes": "UnicodeProcessor.safe_decode",
}


def show_mappings() -> None:
    print("Function replacements:")
    for old, new in REPLACEMENTS.items():
        print(f"  {old} -> {new}")

    print("\nRegex-based replacements for method calls:")
    for pattern, repl in METHOD_PATTERNS.items():
        print(f"  /{pattern}/ -> {repl}")


if __name__ == "__main__":  # pragma: no cover - manual utility
    show_mappings()
