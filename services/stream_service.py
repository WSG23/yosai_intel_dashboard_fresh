import os, asyncio
from .plugin_loader import load_callable
_STREAM = os.getenv("STREAM_HANDLER", "").strip()
_FN = load_callable(_STREAM) if _STREAM else None
async def event_stream(token: str):
    if _FN:
        async for item in _FN(token):
            yield item
        return
    n = 0
    while True:
        n += 1
        yield {"type": "tick", "n": n}
        await asyncio.sleep(1)
