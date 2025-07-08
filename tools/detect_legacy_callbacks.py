from __future__ import annotations

"""Scan code for legacy callback controller usage."""

import re
from pathlib import Path
from typing import Dict, List


class LegacyCallbackDetector:
    """Detect deprecated callback imports and method calls."""

    IMPORT_RE = re.compile(
        r"services\.data_processing\.callback_controller|callbacks\.controller"
    )
    INSTANTIATE_RE = re.compile(r"\bCallbackController\s*\(")
    CALL_RE = re.compile(r"\.fire_event\s*\(")

    def __init__(self) -> None:
        self.imports: Dict[str, List[str]] = {}
        self.instantiations: Dict[str, List[str]] = {}
        self.calls: Dict[str, List[str]] = {}

    def scan_file(self, path: Path) -> None:
        text = path.read_text(errors="ignore")
        imports = self.IMPORT_RE.findall(text)
        if imports:
            self.imports[str(path)] = imports
        inst = self.INSTANTIATE_RE.findall(text)
        if inst:
            self.instantiations[str(path)] = inst
        calls = self.CALL_RE.findall(text)
        if calls:
            self.calls[str(path)] = calls

    def scan(self, root: Path) -> Dict[str, Dict[str, List[str]]]:
        for py in root.rglob("*.py"):
            if "tests" in py.parts:
                continue
            self.scan_file(py)
        return {
            "imports": self.imports,
            "instantiations": self.instantiations,
            "calls": self.calls,
        }
