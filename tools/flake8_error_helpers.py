"""Flake8 plugin to disallow duplicate error helper definitions."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Iterator, Tuple


class ErrorHelperChecker:
    """Detect duplicate error helper definitions outside shared package."""

    name = "error-helper-checker"
    version = "0.1.0"

    def __init__(self, tree: ast.AST, filename: str) -> None:
        self.tree = tree
        self.filename = filename

    def run(self) -> Iterator[Tuple[int, int, str, type]]:
        # pragma: no cover - flake8 hook
        path = Path(self.filename)
        if "tests" in path.parts or path.match("*.pyi"):
            return
        if "shared" in path.parts and "errors" in path.parts:
            return
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "CODE_TO_STATUS":
                        yield (
                            node.lineno,
                            node.col_offset,
                            "ERH001 duplicate CODE_TO_STATUS mapping; "
                            "use shared.errors.types",
                            type(self),
                        )
            if isinstance(node, ast.ClassDef) and node.name == "ServiceError":
                yield (
                    node.lineno,
                    node.col_offset,
                    "ERH002 duplicate ServiceError definition; "
                    "use shared.errors.helpers",
                    type(self),
                )
