from __future__ import annotations

import functools
import time
from typing import Any, Callable, Dict, List


class CallbackProfiler:
    """Simple profiler for callback execution time."""

    def __init__(self) -> None:
        self.records: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    def wrap(self, name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator to profile a callback function."""

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                start = time.perf_counter()
                try:
                    return func(*args, **kwargs)
                finally:
                    duration = time.perf_counter() - start
                    self.records.append({"name": name, "duration": duration})

            return wrapper

        return decorator

    # ------------------------------------------------------------------
    def summary(self) -> Dict[str, float]:
        """Return aggregated profiling results."""
        totals: Dict[str, List[float]] = {}
        for rec in self.records:
            totals.setdefault(rec["name"], []).append(rec["duration"])

        return {name: sum(values) / len(values) for name, values in totals.items()}
