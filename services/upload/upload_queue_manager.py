import asyncio
import heapq
import logging
import threading
import time
import uuid
from typing import Any, Callable, Dict, Iterable, List, Tuple

logger = logging.getLogger(__name__)


class UploadQueueManager:
    """Manage prioritized upload tasks with concurrency control."""

    def __init__(
        self, state: Dict[str, Any] | None = None, *, max_concurrent: int = 3
    ) -> None:
        self.max_concurrent = max_concurrent
        self._lock = threading.Lock()
        self._queue: List[Tuple[int, float, Any]] = []
        self._tasks: Dict[str, asyncio.Task] = {}
        self._state = state if state is not None else {}
        self._load_state()

    # -- Persistence helpers -------------------------------------------------
    def _load_state(self) -> None:
        data = self._state.get("queue_state")
        if not data:
            return
        for priority, ts, item in data.get("queue", []):
            heapq.heappush(self._queue, (priority, ts, item))

    def _save_state(self) -> None:
        self._state["queue_state"] = {
            "queue": list(self._queue),
            "active": list(self._tasks.keys()),
        }

    # -- Public API ----------------------------------------------------------
    def add_files(self, files: Iterable[Any], *, priority: int = 0) -> None:
        """Add ``files`` to the upload queue with the given ``priority``."""
        with self._lock:
            ts = time.time()
            for f in files:
                heapq.heappush(self._queue, (priority, ts, f))
                ts += 1e-6  # ensure stable ordering
            self._save_state()

    def get_queue_status(self) -> Dict[str, Any]:
        """Return counts of queued and active uploads."""
        with self._lock:
            status = {
                "pending": len(self._queue),
                "active": len(self._tasks),
                "max_concurrent": self.max_concurrent,
            }
        return status

    async def process_queue(
        self, handler: Callable[[Any], asyncio.Future | Any]
    ) -> List[Tuple[str, Any]]:
        """Process queued items using ``handler`` respecting concurrency.

        ``handler`` should be a coroutine function accepting a single queued
        item. Completed task results are returned as a list of ``(task_id,
        result)`` tuples. Failed tasks will return the exception instance as the
        result.
        """
        completed: List[Tuple[str, Any]] = []
        with self._lock:
            while self._queue and len(self._tasks) < self.max_concurrent:
                priority, ts, item = heapq.heappop(self._queue)
                task_id = str(uuid.uuid4())
                task = asyncio.create_task(handler(item))
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
