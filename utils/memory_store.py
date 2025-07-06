from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict


@dataclass
class FileMeta:
    filename: str
    path: Path
    rows: int
    columns: int


class MemoryEfficientStore:
    """In-memory metadata store for uploaded files."""

    def __init__(self) -> None:
        self._meta: Dict[str, FileMeta] = {}

    def add(self, filename: str, rows: int, columns: int, path: Path) -> None:
        self._meta[filename] = FileMeta(filename, path, rows, columns)

    def get(self, filename: str) -> FileMeta | None:
        return self._meta.get(filename)

    def all(self) -> Dict[str, Any]:
        return {name: meta.__dict__ for name, meta in self._meta.items()}

    def clear(self) -> None:
        self._meta.clear()


__all__ = ["MemoryEfficientStore", "FileMeta"]
