from __future__ import annotations

"""Report and optionally fix SQL string concatenation patterns."""

import argparse
from pathlib import Path
from typing import Iterable

from scripts.find_sql_concat import apply_fixes, iter_py_files, scan_file


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scan for unsafe SQL concatenation patterns"
    )
    parser.add_argument(
        "paths", nargs="*", default=["."], help="Files or directories to scan"
    )
    parser.add_argument(
        "--auto-fix", action="store_true", help="Automatically rewrite simple cases"
    )
    args = parser.parse_args(list(argv) if argv is not None else None)

    findings: list[tuple[Path, int]] = []
    for file in iter_py_files(args.paths):
        lines = scan_file(file)
        if lines:
            for ln in lines:
                findings.append((file, ln))
            if args.auto_fix:
                apply_fixes(file, lines)

    if findings:
        print("Possible SQL concatenation found:")
        for file, ln in findings:
            print(f"{file}:{ln}")
        if args.auto_fix:
            print(
                "Simple patterns were automatically rewritten. Review remaining occurrences manually."
            )
        return 1

    print("No SQL concatenation patterns detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
