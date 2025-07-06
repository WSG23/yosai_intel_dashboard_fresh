import logging
from typing import Any, Callable

from core.callback_events import CallbackEvent
from core.callback_manager import CallbackManager

logger = logging.getLogger(__name__)

class ProgressEventManager:
    """Wrapper around :class:`CallbackManager` for upload progress."""

    def __init__(self, manager: CallbackManager | None = None) -> None:
        self._manager = manager or CallbackManager()

    def register(self, callback: Callable[[str, int], Any]) -> None:
        self._manager.register_callback(CallbackEvent.ANALYSIS_PROGRESS, callback)

    def unregister(self, callback: Callable[[str, int], Any]) -> None:
        self._manager.unregister_callback(CallbackEvent.ANALYSIS_PROGRESS, callback)

    def emit(self, filename: str, progress: int) -> None:
        self._manager.trigger(CallbackEvent.ANALYSIS_PROGRESS, filename, progress)

progress_manager = ProgressEventManager()

__all__ = ["ProgressEventManager", "progress_manager"]
