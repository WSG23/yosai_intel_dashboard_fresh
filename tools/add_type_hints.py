#!/usr/bin/env python3
"""Script to add simple type hints to Python files.

This utility scans Python source files and adds ``-> Any`` return
annotations to functions lacking them. ``--dry-run`` previews the changes
without writing them back to disk.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

DEF_PATTERN = re.compile(
    r"^(?P<indent>\s*)def (?P<name>[^\(]+)\((?P<args>[^\)]*)\)(?P<suffix>:.*)$"
)


def process_file(path: Path, dry_run: bool) -> bool:
    """Add missing return type hints to ``path``.

    Parameters
    ----------
    path:
        File to update.
    dry_run:
        When ``True`` the file is left untouched and the prospective
        modification is printed instead.

    Returns
    -------
    bool
        ``True`` if changes were required, ``False`` otherwise.
    """

    content = path.read_text().splitlines()
    changed = False

    for index, line in enumerate(content):
        match = DEF_PATTERN.match(line)
        if match and "->" not in line:
            indent = match.group("indent")
            name = match.group("name")
            args = match.group("args")
            suffix = match.group("suffix")
            content[index] = f"{indent}def {name}({args}) -> Any{suffix}"
            changed = True

    if not changed:
        return False

    # ensure Any is imported when modifications were made
    has_any_import = any(
        re.match(r"\s*from typing import .*\bAny\b", line) for line in content
    )
    if not has_any_import:
        insert_at = 0
        for i, line in enumerate(content):
            if line.startswith("from __future__"):
                insert_at = i + 1
        content.insert(insert_at, "from typing import Any")
    new_content = "\n".join(content) + "\n"
    if dry_run:
        print(f"Would update {path}")
        return True

    path.write_text(new_content)
    return True


def gather_files(paths: list[Path]) -> list[Path]:
    """Expand ``paths`` into a list of Python files."""

    files: list[Path] = []
    for path in paths:
        if path.is_file() and path.suffix == ".py":
            files.append(path)
        elif path.is_dir():
            files.extend([p for p in path.rglob("*.py") if p.is_file()])
    return files


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Add simple type hints to Python files"
    )
    parser.add_argument(
        "paths", nargs="+", type=Path, help="Files or directories to process"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without modifying files",
    )
    args = parser.parse_args()

    files = gather_files(args.paths)
    for file_path in files:
        process_file(file_path, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
