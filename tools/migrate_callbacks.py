import ast
import difflib
import shutil
from pathlib import Path
from typing import Dict

MAPPING_MODULES = {
    "security_callback_controller": "core.callback_controller",
    "services.data_processing.callback_controller": "core.callback_controller",
}

NAME_MAP = {
    "SecurityEvent": "CallbackEvent",
    "SecurityCallbackController": "CallbackController",
    "security_callback_controller": "callback_controller",
    "emit_security_event": "fire_event",
    "UnifiedCallbackCoordinator": "TrulyUnifiedCallbacks",
}


def migrate_source(source: str) -> str:
    tree = ast.parse(source)
    changed = False

    class Transformer(ast.NodeTransformer):
        def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST:
            nonlocal changed
            if node.module in MAPPING_MODULES:
                node.module = MAPPING_MODULES[node.module]
                for alias in node.names:
                    if alias.name in NAME_MAP:
                        alias.name = NAME_MAP[alias.name]
                changed = True
            return node

        def visit_Name(self, node: ast.Name) -> ast.AST:
            nonlocal changed
            if node.id in NAME_MAP:
                node.id = NAME_MAP[node.id]
                changed = True
            return node

        def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
            nonlocal changed
            self.generic_visit(node)
            if node.attr in NAME_MAP:
                node.attr = NAME_MAP[node.attr]
                changed = True
            return node

    Transformer().visit(tree)
    if not changed:
        return source
    return ast.unparse(tree)


def migrate_file(path: Path, backup: bool, show_diff: bool) -> bool:
    original = path.read_text()
    new_source = migrate_source(original)
    if new_source == original:
        return False
    if backup:
        shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
    if show_diff:
        for line in difflib.unified_diff(
            original.splitlines(), new_source.splitlines(), fromfile=str(path), tofile=str(path)
        ):
            print(line)
    path.write_text(new_source)
    return True


def validate(root: Path) -> Dict[str, list]:
    from detect_legacy_callbacks import LegacyCallbackDetector

    detector = LegacyCallbackDetector()
    return detector.scan(root)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Migrate legacy callback API usage")
    parser.add_argument("path", nargs="?", default=".", help="project path")
    parser.add_argument("--backup", action="store_true", help="Keep .bak files")
    parser.add_argument("--diff", action="store_true", help="Show unified diff")
    args = parser.parse_args()

    root = Path(args.path)
    migrated = 0
    for py in root.rglob("*.py"):
        if "tests" in py.parts:
            continue
        if migrate_file(py, args.backup, args.diff):
            migrated += 1
    print(f"Migrated {migrated} files")

    report = validate(root)
    if any(report.values()):
        print("Legacy callback usages remain:")
        print(report)
    else:
        print("Migration complete - no legacy callbacks detected")


if __name__ == "__main__":  # pragma: no cover - manual utility
    main()

