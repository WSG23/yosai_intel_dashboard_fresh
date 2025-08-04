#!/usr/bin/env python3
"""Scan repository for common performance anti-patterns."""
from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterable, List, Tuple

Issue = Tuple[str, int, str]


class _Analyzer(ast.NodeVisitor):
    def __init__(self, path: Path) -> None:
        self.path = path
        self.issues: List[Issue] = []

    def visit_BinOp(self, node: ast.BinOp) -> None:  # type: ignore[override]
        if isinstance(node.op, ast.Add) and (
            self._is_str(node.left) or self._is_str(node.right)
        ):
            self.issues.append((str(self.path), node.lineno, "string_concatenation"))
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:  # type: ignore[override]
        if any(isinstance(n, (ast.For, ast.AsyncFor)) for n in node.body):
            self.issues.append((str(self.path), node.lineno, "nested_loops"))
        self.generic_visit(node)

    def visit_ListComp(self, node: ast.ListComp) -> None:  # type: ignore[override]
        iter_node = node.generators[0].iter
        if (
            isinstance(iter_node, ast.Call)
            and getattr(iter_node.func, "id", None) == "range"
            and iter_node.args
            and isinstance(iter_node.args[0], ast.Constant)
            and isinstance(iter_node.args[0].value, int)
            and iter_node.args[0].value > 1000
        ):
            self.issues.append((str(self.path), node.lineno, "large_list_comp"))
        self.generic_visit(node)

    @staticmethod
    def _is_str(node: ast.AST) -> bool:
        return isinstance(node, ast.Constant) and isinstance(node.value, str)


def scan_file(path: Path) -> List[Issue]:
    try:
        tree = ast.parse(path.read_text())
    except SyntaxError:
        return []
    analyzer = _Analyzer(path)
    analyzer.visit(tree)
    return analyzer.issues


def iter_py_files(root: Path) -> Iterable[Path]:
    yield from root.rglob("*.py")


def main(paths: List[str] | None = None) -> int:
    root = Path(".")
    paths = paths or [str(root)]
    findings: List[Issue] = []
    for p_str in paths:
        p = Path(p_str)
        files = [p] if p.is_file() else iter_py_files(p)
        for f in files:
            findings.extend(scan_file(f))
    for file, lineno, kind in findings:
        print(f"{kind}:{file}:{lineno}")
    return 0


if __name__ == "__main__":  # pragma: no cover - manual tool
    import sys

    raise SystemExit(main(sys.argv[1:]))
