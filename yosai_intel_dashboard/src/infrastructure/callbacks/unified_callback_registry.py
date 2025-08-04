from __future__ import annotations

"""Lightweight callback registry used for progress notifications."""

from collections import defaultdict
from enum import Enum, auto
from typing import Callable, DefaultDict, Dict, List


class CallbackType(Enum):
    """Enumeration of callback types supported by the registry."""

    PROGRESS = auto()


class UnifiedCallbackRegistry:
    """Register and trigger callbacks by ``CallbackType`` and ``component_id``."""

    def __init__(self) -> None:  # pragma: no cover - simple container
        self._callbacks: DefaultDict[CallbackType, Dict[str, List[Callable]]]
        self._callbacks = defaultdict(lambda: defaultdict(list))

    # ------------------------------------------------------------------
    def register_callback(
        self, callback_type: CallbackType, callback: Callable, *, component_id: str
    ) -> None:
        """Register *callback* for ``callback_type`` and ``component_id``."""

        self._callbacks[callback_type][component_id].append(callback)

    # ------------------------------------------------------------------
    def trigger_callback(
        self, callback_type: CallbackType, component_id: str, *args, **kwargs
    ) -> None:
        """Trigger all callbacks registered for ``callback_type`` and ``component_id``."""

        for cb in list(self._callbacks.get(callback_type, {}).get(component_id, [])):
            try:
                cb(*args, **kwargs)
            except Exception:
                # Best effort execution – errors should not bubble up
                pass


__all__ = ["CallbackType", "UnifiedCallbackRegistry"]
