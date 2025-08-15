"""Asynchronous health check helpers used in tests."""

from __future__ import annotations

import asyncio
from typing import Awaitable, Callable, Iterable, Tuple, TypedDict

# A probe is a tuple containing the name of the check and an asynchronous
# callable that performs the actual probe.
Probe = Tuple[str, Callable[[], Awaitable[object]]]


class HealthStatus(TypedDict):
    status: str
    checks: dict[str, str]


async def check_with_timeout(
    name: str, probe: Callable[[], Awaitable[object]], timeout_s: float = 1.5
) -> dict[str, str]:
    """Run ``probe`` enforcing ``timeout_s`` and return a result mapping."""
    try:
        await asyncio.wait_for(probe(), timeout=timeout_s)
        return {name: "ok"}
    except Exception as e:  # pragma: no cover - best effort
        return {name: f"fail:{type(e).__name__}"}


async def aggregate(entries: Iterable[Probe]) -> HealthStatus:
    """Execute *entries* and aggregate their results into a status dict."""
    status: HealthStatus = {"status": "ok", "checks": {}}
    checks = status["checks"]
    for name, probe in entries:
        res = await check_with_timeout(name, probe)
        checks.update(res)
        if next(iter(res.values())) != "ok":
            status["status"] = "fail"
    return status
