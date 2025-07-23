#!/usr/bin/env python3
"""Scan Python files for SQL built via string concatenation."""

from __future__ import annotations

import argparse
import ast
from pathlib import Path
from typing import Iterable, List, Tuple

SQL_KEYWORDS = ("select", "insert")


def contains_sql(text: str) -> bool:
    lower = text.lower()
    return any(kw in lower for kw in SQL_KEYWORDS)


def joined_str_has_sql(node: ast.JoinedStr) -> bool:
    for value in node.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            if contains_sql(value.value):
                return True
    return False


def binop_has_sql(node: ast.BinOp) -> bool:
    found = False

    def walk(n: ast.AST) -> None:
        nonlocal found
        if isinstance(n, ast.BinOp) and isinstance(n.op, ast.Add):
            walk(n.left)
            walk(n.right)
        elif isinstance(n, ast.Constant) and isinstance(n.value, str):
            if contains_sql(n.value):
                found = True

    walk(node)
    return found


def scan_file(path: Path) -> List[int]:
    text = path.read_text()
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    lines: List[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr) and joined_str_has_sql(node):
            lines.append(node.lineno)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            if binop_has_sql(node):
                lines.append(node.lineno)
    return sorted(set(lines))


def is_simple_fstring(node: ast.JoinedStr) -> bool:
    for value in node.values:
        if isinstance(value, ast.FormattedValue):
            if not isinstance(value.value, ast.Name):
                return False
    return True


def fix_fstring(node: ast.JoinedStr, source: str) -> Tuple[str, List[str]]:
    parts: List[str] = []
    vars_: List[str] = []
    for value in node.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            parts.append(value.value)
        elif isinstance(value, ast.FormattedValue):
            parts.append("%s")
            seg = ast.get_source_segment(source, value.value)
            vars_.append(seg if seg is not None else ast.unparse(value.value))
        else:
            raise ValueError("Unsupported f-string expression")
    return "".join(parts), vars_


def apply_fixes(path: Path, lines: List[int]) -> None:
    source = path.read_text()
    tree = ast.parse(source)
    to_replace: List[Tuple[int, int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.JoinedStr):
            continue
        if node.lineno not in lines:
            continue
        if not is_simple_fstring(node):
            continue
        new_str, vars_ = fix_fstring(node, source)
        new_expr = (
            repr(new_str)
            + " % ("
            + ", ".join(vars_)
            + ("," if len(vars_) == 1 else ")")
        )
        start_line = node.lineno
        start_col = node.col_offset
        end_line = getattr(node, "end_lineno", node.lineno)
        end_col = getattr(node, "end_col_offset", node.col_offset + 1)
        lines_list = source.splitlines(keepends=True)

        def index(line: int, col: int) -> int:
            return sum(len(chunk) for chunk in lines_list[: line - 1]) + col

        start = index(start_line, start_col)
        end = index(end_line, end_col)
        to_replace.append((start, end, new_expr))

    if not to_replace:
        return

    new_source = source
    for start, end, rep in sorted(to_replace, reverse=True):
        new_source = new_source[:start] + rep + new_source[end:]
    path.write_text(new_source)


def iter_py_files(paths: Iterable[str]) -> Iterable[Path]:
    for p in paths:
        path = Path(p)
        if path.is_file() and path.suffix == ".py":
            yield path
        elif path.is_dir():
            yield from path.rglob("*.py")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Find SQL concatenation")
    parser.add_argument(
        "paths", nargs="*", default=["."], help="Files or directories to scan"
    )
    parser.add_argument(
        "--auto-fix",
        action="store_true",
        help="Replace simple f-strings with placeholders",
    )
    args = parser.parse_args(argv)

    findings: List[Tuple[Path, int]] = []
    for file in iter_py_files(args.paths):
        lines = scan_file(file)
        if lines:
            for ln in lines:
                findings.append((file, ln))
            if args.auto_fix:
                apply_fixes(file, lines)

    if findings:
        print("Possible SQL concatenation found:")
        for file, ln in findings:
            print(f"{file}:{ln}")
        return 1
    print("No SQL concatenation patterns detected.")
    return 0


if __name__ == "__main__":  # pragma: no cover - manual tool
    raise SystemExit(main())
