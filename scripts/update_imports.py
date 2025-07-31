#!/usr/bin/env python3
"""Update import paths to the new clean architecture packages."""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import IO

ROOT = Path(__file__).resolve().parents[1]
# Rewrite patterns for imports.  Only modules that have been fully
# migrated to the new ``yosai_intel_dashboard.src`` layout are included
# here.  Packages such as ``config`` or ``services`` still live at the
# repository root, so rewriting them would break imports.  As new
# packages are migrated they can be added back to this mapping.
PATTERNS = {
    r"\bfrom\s+models(\.|\s)": "from models\\1",
    r"\bimport\s+models(\.|$)": "import models\\1",
    r"\bfrom\s+services(\.|\s)": "from yosai_intel_dashboard.src.services\\1",
    r"\bimport\s+services(\.|$)": "import yosai_intel_dashboard.src.services\\1",
}


def update_file(path: Path, reporter: IO[str] | None = None) -> bool:
    text = path.read_text()
    new_text = text
    for pattern, repl in PATTERNS.items():
        new_text = re.sub(pattern, repl, new_text)
    if new_text != text:
        path.write_text(new_text)
        print(f"Updated {path}")
        if reporter is not None:
            reporter.write(f"{path}\n")
        return True
    return False


def process_paths(paths: list[Path], reporter: IO[str] | None = None) -> None:
    for root in paths:
        for py_file in root.rglob("*.py"):
            update_file(py_file, reporter)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Rewrite import statements")
    parser.add_argument("paths", nargs="*", type=Path, default=[ROOT])
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Run verify_imports after rewriting",
    )
    parser.add_argument("--report", type=Path, help="File to record updated paths")
    args = parser.parse_args(argv)

    report_fh: IO[str] | None = None
    if args.report is not None:
        report_fh = args.report.open("w", encoding="utf-8")

    process_paths(args.paths, reporter=report_fh)

    if report_fh is not None:
        report_fh.close()

    if args.verify:
        from scripts.verify_imports import verify_paths

        return verify_paths(args.paths)
    return 0


if __name__ == "__main__":  # pragma: no cover - manual tool
    raise SystemExit(main())
