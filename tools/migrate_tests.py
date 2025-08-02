#!/usr/bin/env python3
"""Migrate test files to new import conventions.

This utility performs the following steps:

1. Walks the ``tests`` directory looking for ``*.py`` files.
2. Parses each file with :mod:`ast` to inspect import statements.
3. When an optional dependency is imported, inserts
   ``pytest.importorskip("<dep>")`` unless it already exists.
4. Rewrites legacy module paths using :data:`IMPORT_MAP`.
5. For completely removed modules, injects a ``try/except`` block that provides
   a stub via :class:`unittest.mock.Mock`.
6. Writes changes back only when the content differs.  Use ``--dry-run`` to
   preview modifications without touching the files.
"""

from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path
from typing import Dict, Iterable, List, Set

IMPORT_MAP: Dict[str, str] = {
    "analytics.": "services.analytics.",
    "mapping.": "yosai_intel_dashboard.src.mapping.",
    "database.": "yosai_intel_dashboard.src.database.",
}

# Map of fully removed modules to stub names used when creating mocks.
REMOVED_MODULES: Dict[str, str] = {
    # Example: "old.module": "OldModuleStub",
}


def load_optional_deps() -> Set[str]:
    """Return the set of optional dependencies defined for the tests."""

    deps: Set[str] = set()
    req = Path("tests/requirements-extra.txt")
    if not req.exists():
        return deps
    for line in req.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        dep = re.split(r"[<>=]", line)[0].strip()
        if dep:
            deps.add(dep)
    return deps


def imported_modules(tree: ast.AST) -> Set[str]:
    modules: Set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module)
    return modules


def need_importorskip(text: str, modules: Set[str], optional_deps: Set[str]) -> Set[str]:
    needed: Set[str] = set()
    for dep in optional_deps:
        if any(m == dep or m.startswith(f"{dep}.") for m in modules):
            if f'pytest.importorskip("{dep}")' not in text:
                needed.add(dep)
    return needed


def insert_importorskip(lines: List[str], deps: Set[str], last_import: int, has_pytest: bool) -> None:
    if not deps:
        return
    if not has_pytest:
        lines.insert(last_import, "import pytest")
        last_import += 1
        has_pytest = True
    for dep in sorted(deps):
        lines.insert(last_import, f'pytest.importorskip("{dep}")')
        last_import += 1


def replace_legacy_imports(lines: List[str], tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                for old, new in IMPORT_MAP.items():
                    if alias.name.startswith(old):
                        lineno = node.lineno - 1
                        new_name = new + alias.name[len(old) :]
                        lines[lineno] = lines[lineno].replace(alias.name, new_name, 1)
        elif isinstance(node, ast.ImportFrom) and node.module:
            for old, new in IMPORT_MAP.items():
                if node.module.startswith(old):
                    lineno = node.lineno - 1
                    new_module = new + node.module[len(old) :]
                    lines[lineno] = lines[lineno].replace(node.module, new_module, 1)


def stub_removed_modules(lines: List[str], tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.name
                if name in REMOVED_MODULES:
                    target = alias.asname or name.split(".")[-1]
                    stub_name = REMOVED_MODULES[name]
                    lineno = node.lineno - 1
                    block = [
                        "try:",
                        f"    import {name} as {target}",
                        "except ImportError:  # pragma: no cover - removed module",
                        "    from unittest.mock import Mock",
                        f"    {target} = Mock(name='{stub_name}')",
                    ]
                    lines[lineno : lineno + 1] = block
        elif isinstance(node, ast.ImportFrom) and node.module in REMOVED_MODULES:
            lineno = node.lineno - 1
            imports = ", ".join(
                f"{n.name} as {n.asname}" if n.asname else n.name for n in node.names
            )
            targets = [n.asname or n.name for n in node.names]
            block = [
                "try:",
                f"    from {node.module} import {imports}",
                "except ImportError:  # pragma: no cover - removed module",
                "    from unittest.mock import Mock",
            ]
            block.extend(f"    {t} = Mock()" for t in targets)
            lines[lineno : lineno + 1] = block


def process_file(path: Path, dry_run: bool) -> None:
    text = path.read_text()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return

    modules = imported_modules(tree)
    optional_deps = load_optional_deps()
    needed = need_importorskip(text, modules, optional_deps)

    lines = text.splitlines()
    last_import = max(
        (node.lineno for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))),
        default=0,
    )
    has_pytest = "import pytest" in text

    insert_importorskip(lines, needed, last_import, has_pytest)
    replace_legacy_imports(lines, tree)
    stub_removed_modules(lines, tree)

    new_text = "\n".join(lines) + "\n"
    if new_text != text:
        if dry_run:
            print(f"Would update {path}")
        else:
            path.write_text(new_text)
            print(f"Updated {path}")


def main(dry_run: bool) -> None:
    for file in Path("tests").rglob("*.py"):
        process_file(file, dry_run)


if __name__ == "__main__":  # pragma: no cover - utility script
    parser = argparse.ArgumentParser(description="Migrate test imports and dependencies")
    parser.add_argument("--dry-run", action="store_true", help="preview changes without writing")
    args = parser.parse_args()
    main(args.dry_run)
