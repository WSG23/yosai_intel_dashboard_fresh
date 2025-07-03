import asyncio
import threading
import uuid
from typing import Any, Dict, Coroutine

# Simple in-memory async task tracker
_tasks: Dict[str, Dict[str, Any]] = {}

# Background event loop running in a dedicated thread
_loop = asyncio.new_event_loop()
_thread = threading.Thread(target=_loop.run_forever, daemon=True)
_thread.start()


def create_task(coro: Coroutine[Any, Any, Any]) -> str:
    """Schedule ``coro`` and return a task ID."""
    task_id = str(uuid.uuid4())
    _tasks[task_id] = {"progress": 0, "result": None, "done": False}

    async def _runner() -> None:
        _tasks[task_id]["progress"] = 50
        try:
            result = await coro
            _tasks[task_id]["result"] = result
        except Exception as exc:  # pragma: no cover - best effort
            _tasks[task_id]["result"] = exc
        finally:
            _tasks[task_id]["progress"] = 100
            _tasks[task_id]["done"] = True

    _loop.call_soon_threadsafe(_loop.create_task, _runner())
    return task_id


def get_status(task_id: str) -> Dict[str, Any]:
    """Return the status dictionary for ``task_id``."""
    return _tasks.get(task_id, {"progress": 100, "result": None, "done": True})


def clear_task(task_id: str) -> None:
    """Remove completed task from the registry."""
    _tasks.pop(task_id, None)
