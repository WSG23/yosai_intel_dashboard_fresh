from collections import defaultdict
from threading import RLock
from typing import Any, Callable, DefaultDict, Dict, List


class UnifiedCallbackManager:
    """Centralized callback management for analytics."""

    def __init__(self) -> None:
        self.callbacks: DefaultDict[str, List[Callable]] = defaultdict(list)
        self.metrics: DefaultDict[str, Dict[str, Any]] = defaultdict(dict)
        self._lock = RLock()

    def register_analytics_callback(self, event: str, callback: Callable, priority: int = 0) -> None:
        """Register analytics callback with priority."""
        with self._lock:
            self.callbacks[event].append((priority, callback))
            self.callbacks[event].sort(key=lambda x: x[0], reverse=True)

    def trigger_analytics_event(self, event: str, *args: Any, **kwargs: Any) -> List[Any]:
        """Trigger all callbacks for an event."""
        results: List[Any] = []
        with self._lock:
            for _, callback in self.callbacks.get(event, []):
                try:
                    results.append(callback(*args, **kwargs))
                except Exception as exc:  # noqa: BLE001
                    results.append(exc)
        return results

    def consolidate_callback_results(self, results: List[Any]) -> Any:
        """Consolidate multiple callback results."""
        consolidated = []
        for res in results:
            if isinstance(res, list):
                consolidated.extend(res)
            else:
                consolidated.append(res)
        return consolidated
