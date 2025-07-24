#!/usr/bin/env python3
"""Custom import organizer enforcing project conventions."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List


class ImportOrganizer:
    """Apply import conventions to a Python file."""

    FUTURE_LINE = "from __future__ import annotations"

    def organize_file(self, path: Path) -> bool:
        text = path.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()
        changed = False
        if path.name != "__init__.py" and self.FUTURE_LINE not in text:
            insert_at = self._future_insert_index(lines)
            lines.insert(insert_at, self.FUTURE_LINE)
            changed = True
        if changed:
            if lines and not lines[-1].endswith("\n"):
                new_text = "\n".join(lines) + "\n"
            else:
                new_text = "\n".join(lines)
            path.write_text(new_text)
        return changed

    def _future_insert_index(self, lines: List[str]) -> int:
        i = 0
        if i < len(lines) and lines[i].startswith("#!"):
            i += 1
        while i < len(lines) and lines[i].startswith("#"):
            i += 1
        if i < len(lines) and (
            lines[i].startswith('"""') or lines[i].startswith("'''")
        ):
            quote = lines[i][:3]
            i += 1
            while i < len(lines) and quote not in lines[i]:
                i += 1
            if i < len(lines):
                i += 1
        while i < len(lines) and not lines[i].strip():
            i += 1
        return i


class ImportStyleChecker:
    """Verify that files comply with the import conventions."""

    FUTURE_LINE = ImportOrganizer.FUTURE_LINE

    def check_file(self, path: Path) -> List[str]:
        text = path.read_text(encoding="utf-8", errors="ignore")
        errors: List[str] = []
        if path.name != "__init__.py":
            if self.FUTURE_LINE not in text:
                errors.append("missing 'from __future__ import annotations'")
            else:
                lines = text.splitlines()
                pos = next(
                    (i for i, l in enumerate(lines) if self.FUTURE_LINE in l), -1
                )
                for j in range(pos):
                    stripped = lines[j].strip()
                    if stripped.startswith("import ") or stripped.startswith("from "):
                        errors.append("future import not first")
                        break
        return errors


def _collect_files(paths: Iterable[str]) -> List[Path]:
    files: List[Path] = []
    for p in paths:
        path = Path(p)
        if path.is_dir():
            files.extend(sorted(f for f in path.rglob("*.py") if f.is_file()))
        else:
            files.append(path)
    return files


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Organize or check import style")
    parser.add_argument("paths", nargs="*", default=["."], help="files or directories")
    parser.add_argument(
        "--check", action="store_true", help="only check, do not modify"
    )
    args = parser.parse_args(list(argv) if argv else None)

    files = _collect_files(args.paths)
    checker = ImportStyleChecker()
    organizer = ImportOrganizer()

    has_errors = False
    for file in files:
        if args.check:
            errs = checker.check_file(file)
            if errs:
                has_errors = True
                for e in errs:
                    print(f"{file}: {e}")
        else:
            if organizer.organize_file(file):
                print(f"organized {file}")
    return 1 if has_errors else 0


if __name__ == "__main__":  # pragma: no cover - CLI
    raise SystemExit(main())
