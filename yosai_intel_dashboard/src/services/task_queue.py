"""Simple thread-based asynchronous task queue implementation."""

import asyncio
import inspect
import threading
import uuid
from typing import Any, Awaitable, Callable, Dict, Optional

from opentelemetry import context as ot_context

from tracing import propagate_context, trace_async_operation

from .task_queue_protocol import TaskQueueProtocol


class TaskQueue(TaskQueueProtocol):
    """Threaded async task queue."""

    def __init__(self, loop: Optional[asyncio.AbstractEventLoop] = None) -> None:
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._loop = loop or asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

    def create_task(
        self,
        func: Callable[[Callable[[int], None]], Awaitable[Any]] | Awaitable[Any],
        """Schedule an async task and return its identifier."""
    ) -> str:
        task_id = str(uuid.uuid4())
        ctx = ot_context.get_current()
        with self._lock:
            self._tasks[task_id] = {"progress": 0, "result": None, "done": False}

        def _update(pct: int) -> None:
            pct = max(0, min(100, int(pct)))
            with self._lock:
                self._tasks[task_id]["progress"] = pct

        async def _runner() -> None:
            token = ot_context.attach(ctx)
            try:
                if inspect.iscoroutine(func):
                    coro = func
                else:
                    coro = func(_update)
                result = await trace_async_operation("task", task_id, coro)
                with self._lock:
                    self._tasks[task_id]["result"] = result
            except Exception as exc:  # pragma: no cover
                with self._lock:
                    self._tasks[task_id]["result"] = exc
            finally:
                with self._lock:
                    self._tasks[task_id]["progress"] = 100
                    self._tasks[task_id]["done"] = True
                ot_context.detach(token)

        self._loop.call_soon_threadsafe(self._loop.create_task, _runner())
        return task_id

    def get_status(self, task_id: str) -> Dict[str, Any]:
        """Return progress and result for a task."""
        with self._lock:
            status = self._tasks.get(task_id)
            if status is None:
                return {"progress": 100, "result": None, "done": True}
            return dict(status)

    def clear_task(self, task_id: str) -> None:
        """Remove task state once no longer needed."""
        with self._lock:
            self._tasks.pop(task_id, None)


_default_queue = TaskQueue()


def create_task(
    """Add a task to the default queue."""
    func: Callable[[Callable[[int], None]], Awaitable[Any]] | Awaitable[Any],
) -> str:
    return _default_queue.create_task(func)


def get_status(task_id: str) -> Dict[str, Any]:
    """Get status for a task from the default queue."""
    return _default_queue.get_status(task_id)


def clear_task(task_id: str) -> None:
    """Remove a task from the default queue."""
    _default_queue.clear_task(task_id)


__all__ = [
    "TaskQueue",
    "TaskQueueProtocol",
    "create_task",
    "get_status",
    "clear_task",
]
