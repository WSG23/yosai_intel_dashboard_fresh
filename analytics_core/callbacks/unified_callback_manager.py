from __future__ import annotations

"""Unified callback manager used throughout analytics core."""

from typing import Any, List
from core.callback_manager import CallbackManager as _BaseCallbackManager


class UnifiedCallbackManager(_BaseCallbackManager):
    """Thin wrapper around :class:`core.callback_manager.CallbackManager`."""

    def trigger(self, event: Any, *args: Any, **kwargs: Any) -> List[Any]:  # type: ignore[override]
        return super().trigger(event, *args, **kwargs)

    async def trigger_async(self, event: Any, *args: Any, **kwargs: Any) -> List[Any]:  # type: ignore[override]
        return await super().trigger_async(event, *args, **kwargs)


CallbackManager = UnifiedCallbackManager

__all__ = ["UnifiedCallbackManager", "CallbackManager"]
