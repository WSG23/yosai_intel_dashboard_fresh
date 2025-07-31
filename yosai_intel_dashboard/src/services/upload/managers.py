class ChunkedUploadManager:
    """Track progress for chunked file uploads."""

    def __init__(self) -> None:
        self._progress = {}

    def start_file(self, filename: str) -> None:
        self._progress[filename] = 0

    def update_file(self, filename: str, pct: int) -> None:
        self._progress[filename] = max(0, min(100, int(pct)))

    def finish_file(self, filename: str) -> None:
        self._progress[filename] = 100

    def get_progress(self, filename: str) -> int:
        return int(self._progress.get(filename, 0))


class UploadQueueManager:
    """Manage queue of uploads and overall progress."""

    def __init__(self) -> None:
        self.files: list[str] = []
        self.completed: set[str] = set()

    def add_file(self, filename: str) -> None:
        if filename not in self.files:
            self.files.append(filename)

    def mark_complete(self, filename: str) -> None:
        self.completed.add(filename)

    def overall_progress(self) -> int:
        total = len(self.files)
        if total == 0:
            return 0
        pct = int(len(self.completed) / total * 100)
        return max(0, min(100, pct))


__all__ = ["ChunkedUploadManager", "UploadQueueManager"]
