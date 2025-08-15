#!/usr/bin/env python3
"""Ensure cross-module dependencies are documented.

The check scans the ``api``, ``callbacks`` and ``services`` packages for
imports of one another. If such dependencies are found and no ADR documenting
cross-module dependencies exists, the script exits with an error.
"""

from __future__ import annotations

import ast
import pathlib
import sys

MODULES = {
    "api": pathlib.Path("api"),
    "callbacks": pathlib.Path("yosai_intel_dashboard/src/callbacks"),
    "services": pathlib.Path("yosai_intel_dashboard/src/services"),
}

ADR_TOKEN = "cross-module-dependencies"


def _module_for_import(name: str) -> str | None:
    if name.startswith("api"):
        return "api"
    if "callbacks" in name:
        return "callbacks"
    if "services" in name:
        return "services"
    return None


def _collect_violations() -> list[str]:
    violations: list[str] = []
    for module_name, root in MODULES.items():
        for py in root.rglob("*.py"):
            try:
                tree = ast.parse(py.read_text())
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        other = _module_for_import(alias.name)
                        if other and other != module_name:
                            violations.append(f"{py} imports {alias.name}")
                elif isinstance(node, ast.ImportFrom) and node.module:
                    other = _module_for_import(node.module)
                    if other and other != module_name:
                        violations.append(f"{py} imports {node.module}")
    return violations


def main() -> int:
    violations = _collect_violations()
    adr_exists = any(ADR_TOKEN in p.name for p in pathlib.Path("docs/adr").glob("*.md"))
    if violations and not adr_exists:
        print("Cross-module dependencies found without ADR:")
        for v in violations:
            print(f"  - {v}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
