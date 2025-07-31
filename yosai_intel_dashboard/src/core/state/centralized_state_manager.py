from __future__ import annotations

import logging
import threading
from copy import deepcopy
from typing import Any, Callable, Dict, List

logger = logging.getLogger(__name__)

Action = Dict[str, Any]
Reducer = Callable[[Dict[str, Any], Action], Dict[str, Any]]
Subscriber = Callable[[Dict[str, Any], Action], None]


def default_reducer(state: Dict[str, Any], action: Action) -> Dict[str, Any]:
    new_state = state.copy()
    if "payload" in action:
        payload = action["payload"] or {}
        if isinstance(payload, dict):
            new_state.update(payload)
    return new_state


class CentralizedStateManager:
    """Simple Redux-style state storage with dispatch/subscribe APIs."""

    def __init__(
        self,
        initial_state: Dict[str, Any] | None = None,
        reducer: Reducer | None = None,
    ) -> None:
        self._state: Dict[str, Any] = initial_state or {}
        self._reducer: Reducer = reducer or default_reducer
        self._subscribers: List[Subscriber] = []
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    def get_state(self) -> Dict[str, Any]:
        with self._lock:
            return deepcopy(self._state)

    # ------------------------------------------------------------------
    def dispatch(self, action_type: str, payload: Any = None) -> None:
        action = {"type": action_type, "payload": payload}
        with self._lock:
            self._state = self._reducer(self._state, action)
            state_snapshot = deepcopy(self._state)
        for sub in list(self._subscribers):
            try:
                sub(state_snapshot, action)
            except Exception as exc:  # pragma: no cover - subscriber errors
                logger.exception(f"State subscriber error: {exc}")

    # ------------------------------------------------------------------
    def subscribe(self, listener: Subscriber) -> Callable[[], None]:
        self._subscribers.append(listener)

        def unsubscribe() -> None:
            try:
                self._subscribers.remove(listener)
            except ValueError:
                pass

        return unsubscribe

    # ------------------------------------------------------------------
    def replace_reducer(self, reducer: Reducer) -> None:
        self._reducer = reducer
