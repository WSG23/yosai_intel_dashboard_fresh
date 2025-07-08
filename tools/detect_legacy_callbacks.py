import ast
import json
from pathlib import Path
from typing import Dict, List, Set

LEGACY_MODULES = {
    "security_callback_controller",
    "services.data_processing.callback_controller",
    "core.truly_unified_callbacks",
}

LEGACY_NAMES = {
    "SecurityEvent": "CallbackEvent",
    "SecurityCallbackController": "CallbackController",
    "security_callback_controller": "callback_controller",
    "emit_security_event": "fire_event",
    "UnifiedCallbackCoordinator": "TrulyUnifiedCallbacks",
}


def _full_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return f"{_full_name(node.value)}.{node.attr}"
    return ""


class LegacyCallbackDetector:
    """Scan code for legacy callback API usage."""

    def __init__(self) -> None:
        self.imports: Dict[str, Set[str]] = {}
        self.instantiations: Dict[str, Set[str]] = {}
        self.calls: Dict[str, Set[str]] = {}

    # ------------------------------------------------------------------
    def scan_file(self, path: Path) -> None:
        try:
            tree = ast.parse(path.read_text())
        except Exception:
            return

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module in LEGACY_MODULES:
                self.imports.setdefault(str(path), set()).add(node.module)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in LEGACY_MODULES:
                        self.imports.setdefault(str(path), set()).add(alias.name)
            elif isinstance(node, ast.Call):
                name = _full_name(node.func)
                for legacy in LEGACY_NAMES:
                    if legacy in name:
                        self.instantiations.setdefault(str(path), set()).add(name)

            elif isinstance(node, ast.Attribute):
                if node.attr in {"register_callback", "fire_event"}:
                    base = _full_name(node.value)
                    if base in LEGACY_NAMES:
                        self.calls.setdefault(str(path), set()).add(f"{base}.{node.attr}")

    # ------------------------------------------------------------------
    def scan(self, root: Path) -> Dict[str, Dict[str, List[str]]]:
        for py in root.rglob("*.py"):
            if "tests" in py.parts:
                continue
            self.scan_file(py)
        return {
            "imports": {k: sorted(v) for k, v in self.imports.items()},
            "instantiations": {k: sorted(v) for k, v in self.instantiations.items()},
            "calls": {k: sorted(v) for k, v in self.calls.items()},
        }


# ----------------------------------------------------------------------

def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Detect legacy callback APIs")
    parser.add_argument("path", nargs="?", default=".", help="project path")
    args = parser.parse_args()

    detector = LegacyCallbackDetector()
    report = detector.scan(Path(args.path))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":  # pragma: no cover - manual tool
    main()

