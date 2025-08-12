import asyncio
from typing import Callable, Dict

async def check_with_timeout(name: str, probe: Callable, timeout_s: float = 1.5) -> Dict[str, str]:
    try:
        await asyncio.wait_for(probe(), timeout=timeout_s)
        return {name: "ok"}
    except Exception as e:
        return {name: f"fail:{type(e).__name__}"}

async def aggregate(*entries):
    status = {"status": "ok", "checks": {}}
    for name, probe in entries:
        status["checks"].update(await check_with_timeout(name, probe))
        if not list(status["checks"].values())[-1] == "ok":
            status["status"] = "fail"
    return status
