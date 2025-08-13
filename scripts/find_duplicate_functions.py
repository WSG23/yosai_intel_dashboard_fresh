#!/usr/bin/env python3
"""Scan the repository for duplicate function definitions."""
from __future__ import annotations

import argparse
import ast
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass
class FunctionInfo:
    path: Path
    lineno: int
    end_lineno: int
    const_value: object | None
    is_method: bool
    name: str


def _parse_python_file(file_path: Path) -> ast.Module | None:
    """Parse ``file_path`` and return an AST module or ``None`` on syntax error."""
    source = file_path.read_text(encoding="utf-8")
    try:
        return ast.parse(source, filename=str(file_path), type_comments=True)
    except SyntaxError:
        return None


def _extract_functions(
    tree: ast.AST, file_path: Path
) -> list[tuple[str, FunctionInfo]]:
    """Walk ``tree`` collecting function signatures and metadata."""
    functions: list[tuple[str, FunctionInfo]] = []
    stack: list[ast.AST] = []

    class Visitor(ast.NodeVisitor):
        def generic_visit(self, node: ast.AST) -> None:  # pragma: no cover - ast API
            stack.append(node)
            super().generic_visit(node)
            stack.pop()

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # type: ignore[override]
            self._handle(node)
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # type: ignore[override]
            self._handle(node)
            self.generic_visit(node)

        def _handle(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> None:
            body = node.body
            if (
                body
                and isinstance(body[0], ast.Expr)
                and isinstance(body[0].value, ast.Constant)
                and isinstance(body[0].value.value, str)
            ):
                body = body[1:]

            signature = (
                node.name,
                ast.dump(node.args, include_attributes=False),
                ast.dump(
                    ast.Module(body=body, type_ignores=[]), include_attributes=False
                ),
            )

            const_value: object | None = None
            if (
                len(body) == 1
                and isinstance(body[0], ast.Return)
                and isinstance(body[0].value, ast.Constant)
            ):
                const_value = body[0].value.value

            is_method = any(isinstance(n, ast.ClassDef) for n in stack)
            info = FunctionInfo(
                path=file_path,
                lineno=node.lineno,
                end_lineno=node.end_lineno or node.lineno,
                const_value=const_value,
                is_method=is_method,
                name=node.name,
            )
            functions.append(("|".join(signature), info))

    Visitor().visit(tree)
    return functions


def _collect_functions(file_path: Path) -> list[tuple[str, FunctionInfo]]:
    tree = _parse_python_file(file_path)
    if tree is None:
        return []
    return _extract_functions(tree, file_path)


def _module_from_path(path: Path, root: Path) -> str:
    rel = path.with_suffix("").relative_to(root)
    return ".".join(rel.parts)


def find_duplicates(root: Path) -> dict[str, list[FunctionInfo]]:
    dup_map: dict[str, list[FunctionInfo]] = defaultdict(list)
    for file in root.rglob("*.py"):
        for sig, info in _collect_functions(file):
            dup_map[sig].append(info)
    return dup_map


def report_duplicates(dup_map: dict[str, list[FunctionInfo]]) -> None:
    dup_list = [(sig, infos) for sig, infos in dup_map.items() if len(infos) > 1]
    dup_list.sort(key=lambda x: len(x[1]), reverse=True)

    if not dup_list:
        print("No duplicate functions found.")
        return

    print("Duplicate functions found:\n")
    for sig, infos in dup_list:
        print(f"{len(infos)}x {sig}")
        for info in infos:
            print(f"  {info.path}:{info.lineno}")
        print()


def _replace_with_import(info: FunctionInfo, target_module: str, root: Path) -> None:
    path = info.path
    lines = path.read_text(encoding="utf-8").splitlines()
    start = info.lineno - 1
    end = info.end_lineno
    del lines[start:end]

    import_stmt = f"from {target_module} import {info.name}"
    if not any(line.strip() == import_stmt for line in lines):
        insert_pos = 0
        while insert_pos < len(lines) and (
            lines[insert_pos].startswith("#")
            or lines[insert_pos].startswith("from ")
            or lines[insert_pos].startswith("import ")
        ):
            insert_pos += 1
        lines.insert(insert_pos, import_stmt)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def autofix(dup_map: dict[str, list[FunctionInfo]], root: Path) -> None:
    for sig, infos in dup_map.items():
        if len(infos) <= 1:
            continue
        consts = [i.const_value for i in infos]
        if any(c is None for c in consts):
            continue
        if not all(c == consts[0] for c in consts):
            continue
        canonical = infos[0]
        target_module = _module_from_path(canonical.path, root)
        for info in infos[1:]:
            if info.is_method:
                continue
            _replace_with_import(info, target_module, root)
            print(
                f"Replaced {info.path}:{info.lineno}-{info.end_lineno} with import from {target_module}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(description="Find duplicate functions")
    parser.add_argument(
        "--autofix", action="store_true", help="Automatically replace simple duplicates"
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    dup_map = find_duplicates(root)
    report_duplicates(dup_map)

    if args.autofix:
        autofix(dup_map, root)


if __name__ == "__main__":
    main()
