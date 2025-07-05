import logging
from typing import Callable, List, Any

logger = logging.getLogger(__name__)

class ProgressEventManager:
    """Lightweight manager for upload progress events."""

    def __init__(self) -> None:
        self._callbacks: List[Callable[[str, int], Any]] = []

    def register(self, callback: Callable[[str, int], Any]) -> None:
        """Register a progress callback."""
        self._callbacks.append(callback)

    def unregister(self, callback: Callable[[str, int], Any]) -> None:
        """Unregister a callback."""
        self._callbacks = [cb for cb in self._callbacks if cb != callback]

    def emit(self, filename: str, progress: int) -> None:
        """Emit a progress update to all callbacks."""
        for cb in list(self._callbacks):
            try:
                cb(filename, progress)
            except Exception as exc:  # pragma: no cover - best effort
                logger.warning("Progress callback failed: %s", exc)

progress_manager = ProgressEventManager()

__all__ = ["ProgressEventManager", "progress_manager"]
