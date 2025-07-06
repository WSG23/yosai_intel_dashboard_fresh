import asyncio
import inspect
import threading
import uuid
from typing import Any, Awaitable, Callable, Coroutine, Dict

# Simple in-memory async task tracker
_tasks: Dict[str, Dict[str, Any]] = {}
# Lock guarding access to the task dictionary
_lock = threading.Lock()

# Background event loop running in a dedicated thread
_loop = asyncio.new_event_loop()
_thread = threading.Thread(target=_loop.run_forever, daemon=True)
_thread.start()


def create_task(
    func: Callable[[Callable[[int], None]], Awaitable[Any]] | Awaitable[Any]
) -> str:
    """Schedule ``func`` and return a task ID.

    ``func`` may be either a coroutine object or a callable that accepts a
    progress callback and returns a coroutine.  The callback will update
    the internal progress state and may be used by the task to report
    incremental progress.
    """
    
    task_id = str(uuid.uuid4())
    with _lock:
        _tasks[task_id] = {"progress": 0, "result": None, "done": False}

    def _update(pct: int) -> None:
        pct = max(0, min(100, int(pct)))
        with _lock:
            _tasks[task_id]["progress"] = pct

    async def _runner() -> None:
        try:
            if inspect.iscoroutine(func):
                coro = func
            else:
                coro = func(_update)
            result = await coro

            with _lock:
                _tasks[task_id]["result"] = result
        except Exception as exc:  # pragma: no cover - best effort
            with _lock:
                _tasks[task_id]["result"] = exc
        finally:
            with _lock:
                _tasks[task_id]["progress"] = 100
                _tasks[task_id]["done"] = True

    _loop.call_soon_threadsafe(_loop.create_task, _runner())
    return task_id


def get_status(task_id: str) -> Dict[str, Any]:
    """Return the status dictionary for ``task_id``."""
    with _lock:
        status = _tasks.get(task_id)
        if status is None:
            return {"progress": 100, "result": None, "done": True}
        return dict(status)


def clear_task(task_id: str) -> None:
    """Remove completed task from the registry."""
    with _lock:
        _tasks.pop(task_id, None)
