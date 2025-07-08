"""Utilities for cleaning up legacy Unicode APIs."""

from __future__ import annotations

import re
import shutil
from pathlib import Path

# Mapping of deprecated helper functions to their replacements
_DEPRECATED_CALLS = {
    "clean_unicode_surrogates": "clean_unicode_text",
    "handle_surrogate_characters": "clean_unicode_text",
    "safe_encode": "safe_encode_text",
    "safe_decode": "safe_decode_bytes",
    "sanitize_unicode_input": "safe_encode_text",
    "sanitize_data_frame": "sanitize_dataframe",
}


def _replace_imports(text: str) -> str:
    """Return ``text`` with deprecated imports updated."""
    for old, new in _DEPRECATED_CALLS.items():
        # from x import a, b, old, c -> replace name
        pattern = re.compile(rf"(from\s+[\.\w]+\s+import[^\n]*)\b{old}\b")

        def repl(match: re.Match[str]) -> str:
            return match.group(0).replace(old, new)

        text = pattern.sub(repl, text)

        # plain "import module as alias" not handled as names stay same
    return text


def _replace_calls(text: str) -> str:
    """Return ``text`` with calls to deprecated helpers rewritten."""
    for old, new in _DEPRECATED_CALLS.items():
        # direct call foo(old(...)) -> foo(new(...))
        text = re.sub(rf"(?<!\w){old}(?=\s*\()", new, text)
        # attribute call module.old(...) -> module.new(...)
        text = re.sub(rf"(?<=\.){old}(?=\s*\()", new, text)
    return text


def apply_unicode_migration(base_dir: str) -> None:
    """Migrate legacy Unicode helpers under ``base_dir`` to the new API."""

    base = Path(base_dir)
    for path in base.rglob("*.py"):
        try:
            original = path.read_text()
        except Exception:
            continue

        updated = _replace_imports(original)
        updated = _replace_calls(updated)

        if updated != original:
            bak = path.with_suffix(path.suffix + ".bak")
            try:
                shutil.copy2(path, bak)
            except Exception:
                pass
            path.write_text(updated)
