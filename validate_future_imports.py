#!/usr/bin/env python3
"""Validate that __future__ imports are correctly positioned in all Python files."""

import ast
import os
from pathlib import Path


def check_future_imports(file_path: Path):
    """Check if __future__ imports are properly positioned."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)

        future_imports = []
        other_imports = []

        for i, node in enumerate(tree.body):
            if isinstance(node, ast.ImportFrom) and node.module == '__future__':
                future_imports.append(i)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                other_imports.append(i)

        if future_imports and other_imports:
            first_future = min(future_imports)
            first_other = min(other_imports)
            if first_other < first_future:
                return False, (
                    f"Regular import at position {first_other} before __future__ import at {first_future}"
                )
        return True, "OK"
    except Exception as exc:  # pragma: no cover - simple diagnostics
        return False, f"Error parsing file: {exc}"


def scan_project(base: Path | str = Path('.')):
    """Scan all Python files in project for __future__ import issues."""
    base_path = Path(base)
    python_files = [p for p in base_path.rglob('*.py') if not p.name.startswith('.')]
    issues = []

    for file_path in python_files:
        is_valid, message = check_future_imports(file_path)
        if not is_valid:
            issues.append(f"{file_path}: {message}")

    return issues


if __name__ == "__main__":
    print("🔍 Scanning for __future__ import issues...")
    problems = scan_project()
    if problems:
        print("❌ Found issues:")
        for issue in problems:
            print(f"  {issue}")
    else:
        print("✅ All __future__ imports properly positioned!")
