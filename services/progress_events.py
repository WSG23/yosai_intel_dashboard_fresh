from __future__ import annotations
import time
from typing import Iterator
from flask import Response, stream_with_context
from services.task_queue import get_status


class ProgressEventManager:
    """Simple manager streaming task progress via Server-Sent Events."""

    def __init__(self, interval: float = 0.5) -> None:
        self.interval = interval

    def generator(self, task_id: str) -> Iterator[str]:
        """Yield progress values for ``task_id`` until completion."""
        last = None
        while True:
            status = get_status(task_id)
            progress = int(status.get("progress", 0))
            if progress != last:
                yield str(progress)
                last = progress
            if status.get("done"):
                break
            time.sleep(self.interval)

    def stream(self, task_id: str) -> Response:
        """Return an SSE ``Response`` streaming progress for ``task_id``."""
        def _wrap():
            for value in self.generator(task_id):
                yield f"data: {value}\n\n"
        return Response(stream_with_context(_wrap()), mimetype="text/event-stream")


__all__ = ["ProgressEventManager"]
