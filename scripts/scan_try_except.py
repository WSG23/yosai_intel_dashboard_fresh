import argparse
import ast
import difflib
from pathlib import Path
from typing import Dict, List, Tuple


class RedundantTryFinder(ast.NodeVisitor):
    """AST visitor that records potentially redundant try/except blocks."""

    def __init__(self) -> None:
        self.redundant: List[Tuple[int, str, int]] = []
        self._func_stack: List[ast.AST] = []

    def visit_FunctionDef(
        self, node: ast.FunctionDef
    ) -> None:  # type: ignore[override]
        self._func_stack.append(node)
        self.generic_visit(node)
        self._func_stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Try(self, node: ast.Try) -> None:  # type: ignore[override]
        if self._is_redundant(node):
            func = self._func_stack[-1] if self._func_stack else None
            func_name = func.name if isinstance(func, ast.FunctionDef) else ""
            func_line = func.lineno if isinstance(func, ast.FunctionDef) else 0
            self.redundant.append((node.lineno, func_name, func_line))
        self.generic_visit(node)

    def _is_redundant(self, node: ast.Try) -> bool:
        for handler in node.handlers:
            if self._handler_redundant(handler):
                return True
        return False

    def _handler_redundant(self, handler: ast.excepthandler) -> bool:
        # Catching broad exceptions
        is_generic = False
        if handler.type is None:
            is_generic = True
        elif isinstance(handler.type, ast.Name) and handler.type.id in {
            "Exception",
            "BaseException",
        }:
            is_generic = True
        if not is_generic:
            return False

        # Body is empty or just pass
        if not handler.body:
            return True
        if len(handler.body) == 1:
            stmt = handler.body[0]
            if isinstance(stmt, ast.Pass):
                return True
            if isinstance(stmt, ast.Raise):
                # bare raise
                if stmt.exc is None:
                    return True
                if (
                    isinstance(stmt.exc, ast.Name)
                    and handler.name
                    and stmt.exc.id == handler.name
                ):
                    return True
        return False


def find_redundant_trys(path: Path) -> Dict[Path, List[Tuple[int, str, int]]]:
    results: Dict[Path, List[Tuple[int, str, int]]] = {}
    for filepath in path.rglob("*.py"):
        try:
            with filepath.open(encoding="utf-8") as f:
                source = f.read()
            tree = ast.parse(source, filename=str(filepath))
        except Exception:
            continue
        visitor = RedundantTryFinder()
        visitor.visit(tree)
        if visitor.redundant:
            results[filepath] = visitor.redundant
    return results


def generate_patch(file: Path, entries: List[Tuple[int, str, int]]) -> str:
    with file.open(encoding="utf-8") as f:
        original_lines = f.read().splitlines()

    lines = original_lines[:]

    # Insert decorator above functions (process from bottom to top)
    targets = sorted({e[2] for e in entries if e[1]}, reverse=True)
    for func_line in targets:
        idx = func_line - 1
        indent = len(lines[idx]) - len(lines[idx].lstrip())
        decorator = " " * indent + "@handle_errors"
        if idx > 0 and lines[idx - 1].strip() == "@handle_errors":
            continue
        lines.insert(idx, decorator)

    # Ensure import
    import_stmt = "from yosai_intel_dashboard.src.core.error_handling import with_error_handling as handle_errors"
    if not any("handle_errors" in line and "import" in line for line in lines):
        insert_pos = 0
        for i, line in enumerate(lines):
            if line.startswith("#!/"):
                continue
            if line.strip() and not line.startswith("#"):
                insert_pos = i
                break
        lines.insert(insert_pos, import_stmt)

    diff = difflib.unified_diff(
        original_lines,
        lines,
        fromfile=str(file),
        tofile=str(file),
        lineterm="",
    )
    return "\n".join(diff)


def main() -> None:
    parser = argparse.ArgumentParser(description="Scan for redundant try/except blocks")
    parser.add_argument(
        "path", nargs="?", default=".", help="Directory to scan (default: current)"
    )
    parser.add_argument(
        "--patch",
        action="store_true",
        help="Generate patch to wrap functions with handle_errors",
    )
    args = parser.parse_args()

    path = Path(args.path)
    findings = find_redundant_trys(path)
    for file, entries in findings.items():
        for line, func_name, func_line in entries:
            parts = [f"{file}:{line}"]
            if func_name:
                parts.append(f" (in {func_name} at line {func_line})")
            print("".join(parts))
        if args.patch:
            patch = generate_patch(file, entries)
            if patch:
                print("\n" + patch + "\n")


if __name__ == "__main__":
    main()
