#!/usr/bin/env python3
"""Detect SQL queries built with string interpolation."""
from __future__ import annotations

import argparse
import ast
import os
from pathlib import Path
from typing import List, Tuple

SQL_KEYWORDS = {"select", "insert", "update", "delete"}


class SQLVisitor(ast.NodeVisitor):
    def __init__(self, source: str) -> None:
        self.source = source
        self.matches: List[Tuple[int, str]] = []

    def _contains_sql(self, text: str) -> bool:
        lower = text.lower()
        return any(keyword in lower for keyword in SQL_KEYWORDS)

    def visit_JoinedStr(self, node: ast.JoinedStr) -> None:
        if not any(isinstance(v, ast.FormattedValue) for v in node.values):
            return
        text = "".join(
            v.value if isinstance(v, ast.Constant) and isinstance(v.value, str) else ""
            for v in node.values
        )
        if self._contains_sql(text):
            self.matches.append((node.lineno, "f-string"))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Attribute) and node.func.attr == "format":
            if isinstance(node.func.value, ast.Constant) and isinstance(
                node.func.value.value, str
            ):
                if self._contains_sql(node.func.value.value):
                    if node.args or node.keywords:
                        self.matches.append((node.lineno, ".format"))
        self.generic_visit(node)

    def visit_BinOp(self, node: ast.BinOp) -> None:
        if isinstance(node.op, ast.Mod) and isinstance(node.left, ast.Constant):
            if isinstance(node.left.value, str) and self._contains_sql(node.left.value):
                self.matches.append((node.lineno, "%"))
        self.generic_visit(node)


def analyze_file(path: Path) -> List[Tuple[int, str]]:
    try:
        source = path.read_text()
    except Exception:
        return []
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    visitor = SQLVisitor(source)
    visitor.visit(tree)
    return visitor.matches


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Detect SQL queries built with interpolation"
    )
    parser.add_argument(
        "--rewrite", action="store_true", help="Attempt automatic rewriting"
    )
    parser.add_argument("paths", nargs="*", default=["."], help="Paths to search")
    args = parser.parse_args()

    report: List[Tuple[Path, int, str]] = []
    for base in args.paths:
        for root, _dirs, files in os.walk(base):
            for name in files:
                if not name.endswith(".py"):
                    continue
                path = Path(root, name)
                matches = analyze_file(path)
                for lineno, kind in matches:
                    report.append((path, lineno, kind))

    exit_code = 0
    if report:
        for path, lineno, kind in report:
            print(f"{path}:{lineno}: {kind} SQL construction")
        exit_code = 1
    else:
        print("No SQL interpolation patterns found.")

    if args.rewrite:
        print("--rewrite not implemented; manual review needed.")

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
