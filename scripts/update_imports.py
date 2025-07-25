#!/usr/bin/env python3
"""Update import paths to the new clean architecture packages."""
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import IO

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = {
    r"\bfrom\s+core(\.|\s)": "from yosai_intel_dashboard.src.core\\1",
    r"\bimport\s+core(\.|$)": "import yosai_intel_dashboard.src.core\\1",
    r"\bfrom\s+services(\.|\s)": "from yosai_intel_dashboard.src.services\\1",
    r"\bimport\s+services(\.|$)": "import yosai_intel_dashboard.src.services\\1",
    r"\bfrom\s+models(\.|\s)": "from yosai_intel_dashboard.src.core.domain\\1",
    r"\bimport\s+models(\.|$)": "import yosai_intel_dashboard.src.core.domain\\1",
    r"\bfrom\s+config(\.|\s)": "from yosai_intel_dashboard.src.infrastructure.config\\1",
    r"\bimport\s+config(\.|$)": "import yosai_intel_dashboard.src.infrastructure.config\\1",
    r"\bfrom\s+monitoring(\.|\s)": "from yosai_intel_dashboard.src.infrastructure.monitoring\\1",
    r"\bimport\s+monitoring(\.|$)": "import yosai_intel_dashboard.src.infrastructure.monitoring\\1",
    r"\bfrom\s+security(\.|\s)": "from yosai_intel_dashboard.src.infrastructure.security\\1",
    r"\bimport\s+security(\.|$)": "import yosai_intel_dashboard.src.infrastructure.security\\1",
    r"\bfrom\s+api(\.|\s)": "from yosai_intel_dashboard.src.adapters.api\\1",
    r"\bimport\s+api(\.|$)": "import yosai_intel_dashboard.src.adapters.api\\1",
    r"\bfrom\s+plugins(\.|\s)": "from yosai_intel_dashboard.src.adapters.api.plugins\\1",
    r"\bimport\s+plugins(\.|$)": "import yosai_intel_dashboard.src.adapters.api.plugins\\1",
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
