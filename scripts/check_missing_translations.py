#!/usr/bin/env python3
"""Simple check for untranslated strings in .po files."""
from __future__ import annotations

import sys
from pathlib import Path

from babel.messages import pofile


def find_missing_strings() -> list[tuple[Path, str]]:
    missing: list[tuple[Path, str]] = []
    for po_path in Path("translations").rglob("*.po"):
        with po_path.open("r", encoding="utf-8") as f:
            catalog = pofile.read_po(f)

        for message in catalog:
            if message.id and not message.string:
                missing.append((po_path, message.id))
    return missing


def main() -> None:
    missing = find_missing_strings()
    if missing:
        print("Missing translations found:")
        for path, text in missing:
            print(f"{path}: {text}")
        sys.exit(1)

    print("All strings translated.")


if __name__ == "__main__":
    main()
