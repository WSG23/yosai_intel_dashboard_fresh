from __future__ import annotations

import asyncio
import logging
import threading
import time
import uuid
from collections import deque
from typing import Any, Awaitable, Callable, Deque, Dict, Iterable, List, Tuple

logger = logging.getLogger(__name__)


class UploadQueueManager:
    """Manage prioritized upload tasks with concurrency control.

    Parameters
    ----------
    state:
        Optional dictionary used to persist queue state.  Any mapping object may
        be supplied and will be updated in-place when the queue changes.  If not
        provided, an empty dictionary is used.
    max_concurrent:
        Maximum number of concurrent tasks to run.  This can be changed later by
        passing ``max_concurrent`` to :meth:`process_queue`.
    """

    def __init__(
        self,
        state: Dict[str, Any] | None = None,
        *,
        max_concurrent: int = 3,
        task_factory: Callable[[Awaitable[Any]], asyncio.Task] = asyncio.create_task,
    ) -> None:
        self.max_concurrent = max_concurrent
        self._task_factory = task_factory
        self._lock = threading.Lock()
        self._queue: Deque[Tuple[int, float, Any]] = deque()
        self._tasks: Dict[str, asyncio.Task] = {}
        self.files: List[Any] = []
        self.completed: set[Any] = set()
        self._paused = False
        self._state = state if state is not None else {}
        self._load_state()

    # -- Persistence helpers -------------------------------------------------
    def _load_state(self) -> None:
        data = self._state.get("queue_state")
        if not data:
            return
        self._queue = deque(sorted(data.get("queue", [])))
        self._paused = data.get("paused", False)
        self.files = list(data.get("files", []))
        self.completed = set(data.get("completed", []))

    def _save_state(self) -> None:
        self._state["queue_state"] = {
            "queue": list(self._queue),
            "active": list(self._tasks.keys()),
            "paused": self._paused,
            "files": list(self.files),
            "completed": list(self.completed),
        }

    # -- Batch operations ----------------------------------------------------
    def pause(self) -> None:
        """Pause queue processing."""
        with self._lock:
            self._paused = True
            self._save_state()

    def resume(self) -> None:
        """Resume queue processing."""
        with self._lock:
            self._paused = False
            self._save_state()

    def cancel(self) -> None:
        """Cancel all pending and active tasks."""
        with self._lock:
            self._queue.clear()
            for task in list(self._tasks.values()):
                task.cancel()
            self._tasks.clear()
            self._save_state()

    # -- Public API ----------------------------------------------------------
    def add_files(self, files: Iterable[Any], *, priority: int = 0) -> None:
        """Add ``files`` to the upload queue with the given ``priority``."""
        with self._lock:
            ts = time.time()
            for f in files:
                self._queue.append((priority, ts, f))
                if f not in self.files:
                    self.files.append(f)
                ts += 1e-6  # ensure stable ordering
            self._queue = deque(sorted(self._queue))
            self._save_state()

    def add_file(self, file: Any, *, priority: int = 0) -> None:
        """Compatibility wrapper for adding a single file."""
        self.add_files([file], priority=priority)

    def mark_complete(self, file: Any) -> None:
        """Mark ``file`` as completed."""
        with self._lock:
            self.completed.add(file)
            self._save_state()

    def overall_progress(self) -> int:
        total = len(self.files)
        if total == 0:
            return 0
        pct = int(len(self.completed) / total * 100)
        return max(0, min(100, pct))

    def get_queue_status(self) -> Dict[str, Any]:
        """Return counts of queued and active uploads."""
        with self._lock:
            status = {
                "pending": len(self._queue),
                "active": len(self._tasks),
                "paused": self._paused,
                "max_concurrent": self.max_concurrent,
            }
        return status

    async def process_queue(
        self,
        handler: Callable[[Any], asyncio.Future | Any],
        *,
        max_concurrent: int | None = None,
    ) -> List[Tuple[str, Any]]:
        """Process queued items using ``handler`` respecting concurrency.

        ``handler`` should be a coroutine function accepting a single queued
        item. Completed task results are returned as a list of ``(task_id,
        result)`` tuples. Failed tasks will return the exception instance as the
        result.
        """
        if max_concurrent is not None:
            self.max_concurrent = max_concurrent

        completed: List[Tuple[str, Any]] = []
        with self._lock:
            if self._paused:
                return completed
            while self._queue and len(self._tasks) < self.max_concurrent:
                priority, ts, item = self._queue.popleft()
                task_id = str(uuid.uuid4())
                task = self._task_factory(handler(item))
                self._tasks[task_id] = task
            self._save_state()

        for task_id, task in list(self._tasks.items()):
            if task.done():
                try:
                    result = task.result()
                except Exception as exc:  # pragma: no cover - best effort
                    result = exc
                completed.append((task_id, result))
                with self._lock:
                    self._tasks.pop(task_id, None)
                    self._save_state()
        return completed


__all__ = ["UploadQueueManager"]
