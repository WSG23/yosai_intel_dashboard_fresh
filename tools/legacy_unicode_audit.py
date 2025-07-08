import ast
import json
from pathlib import Path
from typing import Dict, List, Set


LEGACY_MODULE = "utils.unicode_utils"
LEGACY_FUNCS: Set[str] = {
    "clean_unicode_text",
    "safe_decode_bytes",
    "safe_encode_text",
    "sanitize_dataframe",
    "safe_encode",
    "safe_decode",
    "handle_surrogate_characters",
    "clean_unicode_surrogates",
    "sanitize_unicode_input",
    "sanitize_data_frame",
}


def _get_full_attr(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_get_full_attr(node.value)}.{node.attr}"
    return ""


class LegacyUnicodeAudit:
    """Scan code for legacy unicode wrapper usage."""

    def __init__(self) -> None:
        self.imports: List[str] = []
        self.calls: Dict[str, List[str]] = {}

    def scan_path(self, path: Path) -> None:
        try:
            tree = ast.parse(path.read_text())
        except Exception:
            return
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module == LEGACY_MODULE:
                    self.imports.append(str(path))
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == LEGACY_MODULE:
                        self.imports.append(str(path))
            elif isinstance(node, ast.Call):
                func_name = _get_full_attr(node.func)
                base, _, attr = func_name.partition(".")
                if func_name.startswith(f"{LEGACY_MODULE}."):
                    self.calls.setdefault(attr, []).append(str(path))
                elif attr == "" and func_name in LEGACY_FUNCS:
                    self.calls.setdefault(func_name, []).append(str(path))

    def scan(self, directory: str) -> Dict[str, List[str]]:
        base = Path(directory)
        for path in base.rglob("*.py"):
            self.scan_path(path)
        return {"imports": self.imports, "calls": self.calls}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Audit for legacy unicode utils")
    parser.add_argument("path", nargs="?", default=".", help="directory to scan")
    args = parser.parse_args()

    audit = LegacyUnicodeAudit()
    report = audit.scan(args.path)
    print(json.dumps(report, indent=2))
