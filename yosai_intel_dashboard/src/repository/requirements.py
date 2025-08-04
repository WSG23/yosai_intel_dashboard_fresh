"""Repository for loading requirement specifications."""
from __future__ import annotations

from pathlib import Path
from typing import List, Protocol


class RequirementsRepository(Protocol):
    """Read required package names."""

    def get_packages(self) -> List[str]:
        """Return a list of required package names."""


class FileRequirementsRepository:
    """Load package requirements from a file."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def get_packages(self) -> List[str]:
        packages: List[str] = []
        with self._path.open("r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                pkg = line.split("==")[0].split(">=")[0].split("~=")[0]
                packages.append(pkg)
        return packages


__all__ = ["RequirementsRepository", "FileRequirementsRepository"]

