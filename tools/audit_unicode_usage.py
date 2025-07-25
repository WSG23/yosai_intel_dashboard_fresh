#!/usr/bin/env python3
"""Scan the repository for legacy ``core.unicode`` imports."""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Dict, Set

TARGET = "core.unicode"


def find_usages(base: Path) -> Dict[str, Set[str]]:
    results: Dict[str, Set[str]] = {}
    for path in base.rglob("*.py"):
        if "unicode_toolkit" in path.parts:
            continue
        try:
            source = path.read_text()
        except Exception:
            continue
        try:
            tree = ast.parse(source)
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod == TARGET or mod.startswith(TARGET + "."):
                    results.setdefault(str(path), set()).add("from")
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.name
                    if name == TARGET or name.startswith(TARGET + "."):
                        results.setdefault(str(path), set()).add("import")
    return results


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    usages = find_usages(repo_root)
    for path, types in sorted(usages.items()):
        print(f"{path}: {', '.join(sorted(types))}")


if __name__ == "__main__":
    main()
