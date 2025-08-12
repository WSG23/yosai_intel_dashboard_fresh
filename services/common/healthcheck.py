import asyncio
from typing import Callable, Dict, Iterable, Tuple

Probe = Tuple[str, Callable[[], asyncio.Future]]


async def check_with_timeout(
    name: str, probe: Callable, timeout_s: float = 1.5
) -> Dict[str, str]:
    try:
        await asyncio.wait_for(probe(), timeout=timeout_s)
        return {name: "ok"}
    except Exception as e:
        return {name: f"fail:{type(e).__name__}"}


async def aggregate(entries: Iterable[Probe]):
    status = {"status": "ok", "checks": {}}
    for name, probe in entries:
        res = await check_with_timeout(name, probe)
        status["checks"].update(res)
        if list(res.values())[0] != "ok":
            status["status"] = "fail"
    return status
