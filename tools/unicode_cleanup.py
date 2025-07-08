from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Dict, List

DEPRECATED_NAMES = {
    "safe_encode",
    "safe_decode",
    "handle_surrogate_characters",
    "clean_unicode_surrogates",
    "sanitize_unicode_input",
    "sanitize_data_frame",
}


def _called_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return ""


def find_deprecated_unicode_usage(base_dir: str) -> Dict[str, List[str]]:
    """Return mapping of deprecated helpers to their usage locations."""

    results: Dict[str, List[str]] = {name: [] for name in DEPRECATED_NAMES}
    base = Path(base_dir)
    for path in base.rglob("*.py"):
        try:
            source = path.read_text()
        except Exception:
            continue
        try:
            tree = ast.parse(source)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == "core.unicode":
                for alias in node.names:
                    if alias.name in DEPRECATED_NAMES:
                        results[alias.name].append(f"{path}:{node.lineno}")
            elif isinstance(node, ast.Call):
                name = _called_name(node.func)
                if name in DEPRECATED_NAMES:
                    results[name].append(f"{path}:{node.lineno}")
    # Drop empty entries
    return {k: v for k, v in results.items() if v}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Scan project for deprecated Unicode helper usage"
    )
    parser.add_argument("path", nargs="?", default=".")
    args = parser.parse_args()

    report = find_deprecated_unicode_usage(args.path)
    print(json.dumps(report, indent=2))
