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
    # Core domain imports
    r"\bfrom\s+models\.base\s+import": "from yosai_intel_dashboard.src.core.domain.entities.base import",
    r"\bfrom\s+models\.entities\s+import": "from yosai_intel_dashboard.src.core.domain.entities.entities import",
    r"\bfrom\s+models\.events\s+import": "from yosai_intel_dashboard.src.core.domain.entities.events import",
    r"\bfrom\s+models\.enums\s+import": "from yosai_intel_dashboard.src.core.domain.value_objects.enums import",

    # Callback system imports
    r"\bfrom\s+core\.callbacks\s+import\s+UnifiedCallbackManager": "from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks",
    r"\bfrom\s+core\.callback_controller\s+import\s+CallbackController": "from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks",
    r"\bfrom\s+core\.truly_unified_callbacks\s+import\s+TrulyUnifiedCallbacks": "from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks",
    r"\bfrom\s+core\.callback_events\s+import\s+CallbackEvent": "from yosai_intel_dashboard.src.infrastructure.callbacks.events import CallbackEvent",
    r"\bfrom\s+services\.security_callback_controller\s+import": "from yosai_intel_dashboard.src.infrastructure.callbacks.security_controller import",

    # Service imports
    r"\bfrom\s+services\.analytics_service\s+import": "from yosai_intel_dashboard.src.services.analytics.analytics_service import",
    r"\bfrom\s+services\.analytics\.": "from yosai_intel_dashboard.src.services.analytics.",
    r"\bfrom\s+services\.upload\.": "from yosai_intel_dashboard.src.services.upload.",
    r"\bfrom\s+services\.data_processing\.": "from yosai_intel_dashboard.src.services.data_processing.",

    # Infrastructure imports
    r"\bfrom\s+config\.": "from yosai_intel_dashboard.src.infrastructure.config.",
    r"\bfrom\s+core\.service_container\s+import": "from yosai_intel_dashboard.src.infrastructure.di.service_container import",
    r"\bfrom\s+core\.protocols\s+import": "from yosai_intel_dashboard.src.core.interfaces.protocols import",
    r"\bfrom\s+services\.interfaces\s+import": "from yosai_intel_dashboard.src.core.interfaces.service_protocols import",

    # UI imports
    r"\bfrom\s+components\.": "from yosai_intel_dashboard.src.adapters.ui.components.",
    r"\bfrom\s+pages\.": "from yosai_intel_dashboard.src.adapters.ui.pages.",
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
