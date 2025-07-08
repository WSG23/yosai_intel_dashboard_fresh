from __future__ import annotations

"""Utilities for rewriting legacy callback imports."""

import difflib
from pathlib import Path

_REPLACEMENTS = {
    "core.truly_unified_callbacks": "core.truly_unified_callbacks",
    "core.truly_unified_callbacks": "core.truly_unified_callbacks",
}


def migrate_file(path: Path, *, backup: bool = False, show_diff: bool = False) -> bool:
    """Rewrite legacy callback imports in ``path``.

    Returns ``True`` if the file was modified.
    """
    text = path.read_text()
    new_text = text
    for old, new in _REPLACEMENTS.items():
        new_text = new_text.replace(old, new)

    if new_text == text:
        return False

    if backup:
        backup_path = path.with_suffix(path.suffix + ".bak")
        backup_path.write_text(text)

    path.write_text(new_text)

    if show_diff:
        diff = difflib.unified_diff(
            text.splitlines(True),
            new_text.splitlines(True),
            fromfile=str(path),
            tofile=str(path),
        )
        print("".join(diff))

    return True
