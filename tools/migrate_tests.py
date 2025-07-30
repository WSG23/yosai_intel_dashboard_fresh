from __future__ import annotations

"""Utility for migrating tests away from ``sys.modules`` stubs.

The script comments out assignments to ``sys.modules`` and instead imports
protocol test doubles from ``tests.stubs``. The generated code directly
replaces the stubbed module in ``sys.modules`` so tests run against the
lightweight doubles without further manual edits.
"""

import argparse
import ast
import difflib
from pathlib import Path
from typing import Iterable, List, Optional


class SysModulesVisitor(ast.NodeVisitor):
    """Find sys.modules modifications in a file."""

    def __init__(self) -> None:
        self.patches: List[tuple[int, int, str]] = []

    def visit_Assign(self, node: ast.Assign) -> None:
        for target in node.targets:
            mod = self._get_sys_modules_key(target)
            if mod:
                end = getattr(node, "end_lineno", node.lineno)
                self.patches.append((node.lineno, end, mod))
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        # sys.modules.setdefault("foo", value)
        if isinstance(node.func, ast.Attribute) and self._is_sys_modules(
            node.func.value
        ):
            if node.func.attr in {"setdefault", "pop"} and node.args:
                mod = self._get_const(node.args[0])
                if mod:
                    end = getattr(node, "end_lineno", node.lineno)
                    self.patches.append((node.lineno, end, mod))

        # monkeypatch.setitem(sys.modules, "foo", value)
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr in {"setitem", "delitem"}
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "monkeypatch"
            and node.args
        ):
            if self._is_sys_modules(node.args[0]):
                mod = self._get_const(node.args[1]) if len(node.args) > 1 else None
                if mod:
                    end = getattr(node, "end_lineno", node.lineno)
                    self.patches.append((node.lineno, end, mod))
        self.generic_visit(node)

    # --------------------------------------------------------------
    def _is_sys_modules(self, node: ast.AST) -> bool:
        return (
            isinstance(node, ast.Attribute)
            and isinstance(node.value, ast.Name)
            and node.value.id == "sys"
            and node.attr == "modules"
        )

    def _get_sys_modules_key(self, node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Subscript) and self._is_sys_modules(node.value):
            return self._get_const(node.slice)
        return None

    def _get_const(self, node: ast.AST) -> Optional[str]:
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None


def find_patches(path: Path) -> List[tuple[int, int, str]]:
    try:
        tree = ast.parse(path.read_text())
    except Exception:
        return []
    visitor = SysModulesVisitor()
    visitor.visit(tree)
    return visitor.patches


def apply_patches(text: str, patches: Iterable[tuple[int, int, str]]) -> str:
    lines = text.splitlines()

    def _stub_var(mod_name: str) -> str:
        return mod_name.replace(".", "_") + "_stub"

    for start, end, mod in sorted(patches, key=lambda t: t[0], reverse=True):
        for i in range(start - 1, end):
            lines[i] = f"# {lines[i]}"

        stub_var = _stub_var(mod)
        stub_import = f"import tests.stubs.{mod} as {stub_var}"
        assign_line = f"sys.modules['{mod}'] = {stub_var}"

        lines.insert(end, stub_import)
        lines.insert(end + 1, assign_line)

    return "\n".join(lines) + "\n"


def process_file(path: Path, apply: bool, show_diff: bool) -> None:
    text = path.read_text()
    patches = find_patches(path)
    if not patches:
        return
    new_text = apply_patches(text, patches)
    if show_diff:
        diff = difflib.unified_diff(
            text.splitlines(),
            new_text.splitlines(),
            fromfile=str(path),
            tofile=str(path),
        )
        print("\n".join(diff))
    if apply:
        path.write_text(new_text)


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(
        description="Rewrite sys.modules stubs to use protocol test doubles"
    )
    parser.add_argument(
        "paths", nargs="*", default=["tests"], help="files or directories to scan"
    )
    parser.add_argument("--apply", action="store_true", help="write changes to disk")
    parser.add_argument("--diff", action="store_true", help="show unified diff")
    args = parser.parse_args(argv[1:])

    for p in args.paths:
        path = Path(p)
        if path.is_dir():
            for file in path.rglob("*.py"):
                process_file(file, args.apply, args.diff)
        elif path.is_file():
            process_file(path, args.apply, args.diff)


if __name__ == "__main__":  # pragma: no cover - manual utility
    import sys

    main(sys.argv)
