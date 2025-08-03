"""Simple thread-based asynchronous task queue implementation."""

from __future__ import annotations

import asyncio
import inspect
import queue as queue_module
import threading
import uuid
from typing import Any, Awaitable, Callable, Dict

from opentelemetry import context as ot_context

from tracing import trace_async_operation

from .task_queue_protocol import TaskQueueProtocol


class TaskQueue(TaskQueueProtocol):
    """Threaded async task queue with basic idempotency support."""

    def __init__(self, workers: int = 1) -> None:
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._queue: queue_module.Queue[tuple[str, Any, Any]] = queue_module.Queue()
        self._idempotency: Dict[str, str] = {}
        self._task_keys: Dict[str, str] = {}
        for _ in range(max(1, workers)):
            thread = threading.Thread(target=self._worker, daemon=True)
            thread.start()

    def _worker(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        while True:
            item = self._queue.get()
            if item is None:
                break
            task_id, ctx, func = item

            def _update(pct: int) -> None:
                pct = max(0, min(100, int(pct)))
                with self._lock:
                    self._tasks[task_id]["progress"] = pct

            async def _runner() -> None:
                token = ot_context.attach(ctx)
                try:
                    if inspect.iscoroutine(func):
                        coro = func
                    elif inspect.iscoroutinefunction(func):
                        if len(inspect.signature(func).parameters) == 0:
                            coro = func()
                        else:
                            coro = func(_update)
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

            loop.run_until_complete(_runner())
            self._queue.task_done()

    def create_task(
        self,
        func: Callable[[Callable[[int], None]], Awaitable[Any]] | Awaitable[Any],
        *,
        idempotency_key: str | None = None,
    ) -> str:
        """Schedule an async task and return its identifier."""
        ctx = ot_context.get_current()
        with self._lock:
            if idempotency_key is not None:
                existing = self._idempotency.get(idempotency_key)
                if existing is not None:
                    return existing
            task_id = str(uuid.uuid4())
            self._tasks[task_id] = {"progress": 0, "result": None, "done": False}
            if idempotency_key is not None:
                self._idempotency[idempotency_key] = task_id
                self._task_keys[task_id] = idempotency_key

        self._queue.put((task_id, ctx, func))
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
            key = self._task_keys.pop(task_id, None)
            if key is not None:
                self._idempotency.pop(key, None)


_default_queue = TaskQueue()


def create_task(
    func: Callable[[Callable[[int], None]], Awaitable[Any]] | Awaitable[Any],
    *,
    idempotency_key: str | None = None,
) -> str:
    """Add a task to the default queue."""
    return _default_queue.create_task(func, idempotency_key=idempotency_key)


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
