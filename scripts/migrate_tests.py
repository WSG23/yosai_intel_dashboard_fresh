#!/usr/bin/env python3
"""Automate migration of test modules.

This script rewrites ``sys.modules`` stubbing patterns in ``tests/`` to use the
helpers provided in ``tests.import_helpers``.  It also updates imports to pull
fixtures from ``tests.config``.

Any unhandled ``sys.modules`` manipulations are reported as TODO items for
manual follow-up.
"""
from __future__ import annotations

import pathlib
import re

TESTS_DIR = pathlib.Path(__file__).resolve().parents[1] / "tests"

# Regex patterns for sys.modules manipulations
SETDEFAULT_RE = re.compile(
    r"^(\s*)sys\.modules\.setdefault\((['\"])([^'\"]+)\2,\s*(.*)\)\s*(#.*)?$"
)
ASSIGN_RE = re.compile(r"^(\s*)sys\.modules\[(['\"])([^'\"]+)\2\]\s*=\s*(.+)")
MONKEYPATCH_RE = re.compile(
    r"^(\s*)monkeypatch\.setitem\(sys\.modules,\s*(['\"])([^'\"]+)\2,\s*(.*)\)\s*(#.*)?$"
)

# Regex for fixture import replacements
FAKE_CONFIG_RE = re.compile(r"^(\s*)from\s+tests\.fake_configuration\s+import\s+(.*)")
FAKE_CONFIG_IMPORT_AS_RE = re.compile(
    r"^(\s*)import\s+tests\.fake_configuration\s+as\s+(\w+)"
)

IMPORT_HELPERS_LINE = "from tests.import_helpers import safe_import, import_optional"


def ensure_import_helpers(lines: list[str]) -> None:
    """Insert import for helper functions if not already present."""
    if any("tests.import_helpers" in line for line in lines):
        return
    insert_pos = 0
    for idx, line in enumerate(lines):
        if line.startswith("from") or line.startswith("import"):
            insert_pos = idx + 1
        elif line.strip():
            break
    lines.insert(insert_pos, IMPORT_HELPERS_LINE)


def replace_sys_modules(lines: list[str]) -> tuple[list[str], list[tuple[int, str]]]:
    """Replace sys.modules patterns returning modified lines and TODO items."""
    todos: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        m = SETDEFAULT_RE.match(line)
        if m:
            indent, name, stub, comment = (
                m.group(1),
                m.group(3),
                m.group(4),
                m.group(5) or "",
            )
            call = f"safe_import('{name}', {stub})"
            lines[i] = f"{indent}{call}{comment}"
            continue
        m = ASSIGN_RE.match(line)
        if m:
            indent, name, stub = m.group(1), m.group(3), m.group(4)
            call = f"safe_import('{name}', {stub})"
            lines[i] = f"{indent}{call}"
            continue
        m = MONKEYPATCH_RE.match(line)
        if m:
            indent, name, stub, comment = (
                m.group(1),
                m.group(3),
                m.group(4),
                m.group(5) or "",
            )
            call = f"safe_import('{name}', {stub})"
            lines[i] = f"{indent}{call}{comment}"
            continue
        if (
            "sys.modules" in line
            and "safe_import" not in line
            and "import_optional" not in line
        ):
            todos.append((i + 1, line.rstrip()))
    return lines, todos


def replace_fixture_imports(lines: list[str]) -> list[str]:
    """Update fixture imports to use ``tests.config``."""
    for i, line in enumerate(lines):
        m = FAKE_CONFIG_RE.match(line)
        if m:
            indent, rest = m.groups()
            lines[i] = f"{indent}from tests.config import {rest}"
            continue
        m = FAKE_CONFIG_IMPORT_AS_RE.match(line)
        if m:
            indent, alias = m.groups()
            lines[i] = f"{indent}import tests.config as {alias}"
    return lines


def process_file(path: pathlib.Path) -> list[tuple[pathlib.Path, int, str]]:
    """Rewrite a test file replacing legacy ``sys.modules`` patterns.

    Returns a list of ``(path, line number, content)`` tuples for any remaining
    ``sys.modules`` manipulations that require manual follow-up.
    """
    text = path.read_text().splitlines()
    original_lines = list(text)
    text = replace_fixture_imports(text)
    text, todos = replace_sys_modules(text)
    if text != original_lines:
        ensure_import_helpers(text)
        path.write_text("\n".join(text) + "\n")
    return [(path, ln, content) for ln, content in todos]


def main() -> None:
    """Run migrations over the test suite and report remaining TODO items."""
    todos: list[tuple[pathlib.Path, int, str]] = []
    for py_file in TESTS_DIR.rglob("*.py"):
        if py_file == TESTS_DIR / "config.py":
            continue
        todos.extend(process_file(py_file))
    if todos:
        print("\nTODO: manual review required for the following sys.modules usages:")
        for path, line_no, content in todos:
            print(f"- {path}:{line_no}: {content}")
    else:
        print("All sys.modules manipulations migrated successfully.")


if __name__ == "__main__":
    main()
