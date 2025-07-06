from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from ..error_handling import ErrorSeverity, error_handler, with_retry

logger = logging.getLogger(__name__)


@dataclass
class Operation:
    """Represent a single callback operation."""

    name: str
    func: Callable[..., Any]
    timeout: Optional[float] = None
    retries: int = 0


class UnifiedCallbackManager:
    """Manage groups of callback operations with error handling."""

    def __init__(self) -> None:
        self._groups: Dict[str, List[Operation]] = defaultdict(list)

    # ------------------------------------------------------------------
    def register_operation(
        self,
        group: str,
        func: Callable[..., Any],
        *,
        name: Optional[str] = None,
        timeout: Optional[float] = None,
        retries: int = 0,
    ) -> None:
        """Register an operation under a group name."""
        op = Operation(name or func.__name__, func, timeout, retries)
        self._groups[group].append(op)

    # ------------------------------------------------------------------
    def clear_group(self, group: str) -> None:
        self._groups.pop(group, None)

    # ------------------------------------------------------------------
    def execute_group(self, group: str, *args: Any, **kwargs: Any) -> List[Any]:
        """Execute all operations in a group sequentially."""
        results: List[Any] = []
        for op in list(self._groups.get(group, [])):
            wrapped = with_retry(max_attempts=op.retries + 1)(op.func)
            start = time.perf_counter()
            try:
                result = wrapped(*args, **kwargs)
                duration = time.perf_counter() - start
                if op.timeout and duration > op.timeout:
                    raise TimeoutError(
                        f"Operation {op.name} exceeded {op.timeout}s"
                    )
                results.append(result)
            except Exception as exc:  # pragma: no cover - log and continue
                error_handler.handle_error(
                    exc,
                    severity=ErrorSeverity.HIGH,
                    context={"operation": op.name, "group": group},
                )
                results.append(None)
        return results

