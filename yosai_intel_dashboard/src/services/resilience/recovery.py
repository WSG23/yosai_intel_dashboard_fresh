from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable, Optional

from .metrics import (
    dependency_recovery_attempts,
    dependency_recovery_successes,
)


async def _is_open(circuit: Any) -> bool:
    if hasattr(circuit, "allows_request"):
        return not await circuit.allows_request()
    state = getattr(circuit, "state", "")
    return state == "open"


async def _reset(circuit: Any) -> None:
    if hasattr(circuit, "record_success"):
        await circuit.record_success()
    elif hasattr(circuit, "reset"):
        circuit.reset()


async def monitor_dependency(
    name: str,
    circuit: Any,
    check: Callable[[], Awaitable[bool]],
    on_recover: Optional[Callable[[], Awaitable[None]]] = None,
    *,
    interval: float = 30.0,
    logger: Optional[logging.Logger] = None,
) -> None:
    """Background task monitoring a dependency for recovery.

    Parameters
    ----------
    name:
        Identifier for logging and metrics.
    circuit:
        Circuit breaker protecting the dependency.
    check:
        Async callable returning ``True`` when the dependency is healthy.
    on_recover:
        Optional async callable invoked after recovery.
    interval:
        Seconds between recovery attempts while the circuit is open.
    logger:
        Logger instance; falls back to module logger.
    """

    log = logger or logging.getLogger(__name__)

    while True:
        await asyncio.sleep(interval)
        if not await _is_open(circuit):
            continue

        dependency_recovery_attempts.labels(name).inc()
        try:
            healthy = await check()
        except Exception:
            healthy = False

        if healthy:
            dependency_recovery_successes.labels(name).inc()
            await _reset(circuit)
            if on_recover is not None:
                await on_recover()
            log.info("%s recovered", name)
        else:
            log.warning("Recovery attempt for %s failed", name)
