"""Thread-safe store for device mapping results produced by AI."""

import threading
from typing import Any, Dict


class AIMappingStore:
    """Thread-safe store for device AI mappings."""

    def __init__(self):
        self._mappings: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def get(self, device: str) -> Dict[str, Any]:
        with self._lock:
            return self._mappings.get(device, {})

    def set(self, device: str, mapping: Dict[str, Any]) -> None:
        with self._lock:
            self._mappings[device] = mapping

    def update(self, mappings: Dict[str, Dict[str, Any]]) -> None:
        with self._lock:
            self._mappings.update(mappings)

    def clear(self) -> None:
        with self._lock:
            self._mappings.clear()

    def all(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return dict(self._mappings)

    def __len__(self) -> int:
        with self._lock:
            return len(self._mappings)


ai_mapping_store = AIMappingStore()

__all__ = ["AIMappingStore", "ai_mapping_store"]
