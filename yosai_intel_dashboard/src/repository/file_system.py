"""Filesystem repository utilities."""
from __future__ import annotations

from pathlib import Path
from typing import Protocol


class FileRepository(Protocol):
    """Basic file system operations."""

    def write_text(self, path: str | Path, data: str) -> None: ...
    def read_text(self, path: str | Path) -> str: ...


class LocalFileRepository:
    """Concrete repository using the local filesystem."""

    def write_text(self, path: str | Path, data: str) -> None:
        Path(path).write_text(data, encoding="utf-8")

    def read_text(self, path: str | Path) -> str:
        return Path(path).read_text(encoding="utf-8")
