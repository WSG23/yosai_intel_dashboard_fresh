from __future__ import annotations

"""Debug utilities for tracing callback registrations."""

import functools
import inspect
import logging
import sys
import time
from typing import Any, Dict, List, Tuple

logger = logging.getLogger(__name__)

# In-memory log of registration events: (callback_id, timestamp, caller_module)
_REGISTRATION_LOG: List[Tuple[str, float, str]] = []


def debug_callback_registration_flow(target_class: Any | None = None) -> None:
    """Patch ``handle_register_with_deduplication`` on *target_class*.

    The wrapper logs the caller's module name and the callback ID along with
    the registration time. When *target_class* is ``None`` the function tries
    to import ``TrulyUnifiedCallbacks`` from ``core.truly_unified_callbacks``.
    """

    if target_class is None:
        try:
            from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks

            target_class = TrulyUnifiedCallbacks
        except Exception:  # pragma: no cover - best effort
            logger.warning("TrulyUnifiedCallbacks unavailable")
            return

    original = getattr(target_class, "handle_register_with_deduplication", None)
    if original is None:
        logger.warning(
            f"handle_register_with_deduplication not found on {target_class}"
        )
        return

    @functools.wraps(original)
    def wrapper(self: Any, *args: Any, **kwargs: Any) -> Any:
        frame = inspect.stack()[1]
        module_name = frame.frame.f_globals.get("__name__", "unknown")
        callback_id = kwargs.get("callback_id") or "unknown"
        timestamp = time.time()
        _REGISTRATION_LOG.append((callback_id, timestamp, module_name))
        logger.debug(
            f"Registering {callback_id} from {module_name} via handle_register_with_deduplication"
        )
        return original(self, *args, **kwargs)

    setattr(target_class, "handle_register_with_deduplication", wrapper)


def find_repeated_imports() -> List[str]:
    """Return module names imported more than once."""
    counts: Dict[str, int] = {}
    for name, mod in sys.modules.items():
        path = getattr(mod, "__file__", None)
        if not path:
            continue
        counts[path] = counts.get(path, 0) + 1
    return [name for name, count in counts.items() if count > 1]


def print_registration_report() -> None:
    """Print a summary report of captured registration events."""
    for cid, ts, module in _REGISTRATION_LOG:
        timestr = time.strftime("%H:%M:%S", time.localtime(ts))
        print(f"{timestr} - {module} -> {cid}")

    duplicates = find_repeated_imports()
    if duplicates:
        print("\nRepeated imports detected:")
        for mod in duplicates:
            print(f"  {mod}")


if __name__ == "__main__":
    debug_callback_registration_flow()
    print_registration_report()
