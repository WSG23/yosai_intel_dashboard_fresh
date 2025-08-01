from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from yosai_intel_dashboard.src.mapping.core.interfaces import StorageInterface


class JsonStorage(StorageInterface):
    """Persist mappings to a JSON file."""

    def __init__(self, path: str) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        if self.path.exists():
            with open(self.path, "r", encoding="utf-8", errors="replace") as fh:
                return json.load(fh)
        return {}

    def save(self, data: Dict[str, Any]) -> None:
        with open(self.path, "w", encoding="utf-8", errors="replace") as fh:
            json.dump(data, fh, indent=2)


class MemoryStorage(StorageInterface):
    """In-memory storage useful for testing."""

    def __init__(self) -> None:
        self._data: Dict[str, Any] = {}

    def load(self) -> Dict[str, Any]:
        return dict(self._data)

    def save(self, data: Dict[str, Any]) -> None:
        self._data = dict(data)
