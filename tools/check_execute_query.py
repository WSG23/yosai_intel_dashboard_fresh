#!/usr/bin/env python3
"""Lint to ensure execute_query isn't called with factory.get_connection()."""
from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Tuple


def _is_factory_get_connection(call: ast.Call) -> bool:
    return (
        isinstance(call.func, ast.Attribute)
        and isinstance(call.func.value, ast.Name)
        and call.func.value.id == "factory"
        and call.func.attr == "get_connection"
    )


def _check_file(path: Path) -> List[Tuple[int, int]]:
    try:
        source = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []
    issues: List[Tuple[int, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "execute_query":
                if (
                    node.args
                    and isinstance(node.args[0], ast.Call)
                    and _is_factory_get_connection(node.args[0])
                ):
                    issues.append((node.lineno, node.col_offset))
            elif isinstance(func, ast.Attribute) and func.attr == "execute_query":
                if (
                    node.args
                    and isinstance(node.args[0], ast.Call)
                    and _is_factory_get_connection(node.args[0])
                ):
                    issues.append((node.lineno, node.col_offset))
    return issues


def find_violations(paths: Iterable[Path]) -> Dict[Path, List[Tuple[int, int]]]:
    result: Dict[Path, List[Tuple[int, int]]] = {}
    for path in paths:
        if path.is_dir():
            for file in path.rglob("*.py"):
                issues = _check_file(file)
                if issues:
                    result[file] = issues
        elif path.is_file() and path.suffix == ".py":
            issues = _check_file(path)
            if issues:
                result[path] = issues
    return result


def main(argv: List[str]) -> int:
    paths = [Path(p) for p in (argv or ["."])]
    violations = find_violations(paths)
    if violations:
        for file, entries in violations.items():
            for line, col in entries:
                print(
                    f"{file}:{line}:{col}: avoid execute_query without 'with factory.get_connection()'"
                )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
