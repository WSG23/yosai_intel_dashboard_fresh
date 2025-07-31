import json
import logging
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

from config.connection_retry import ConnectionRetryManager, RetryConfig
from config.constants import DEFAULT_CHUNK_SIZE, DataProcessingLimits
from config.protocols import ConnectionRetryManagerProtocol, RetryConfigProtocol
from utils.upload_store import UploadedDataStore

logger = logging.getLogger(__name__)


@dataclass
class UploadMetadata:
    """Persistent state for an in-progress upload."""

    filename: str
    total_rows: int
    chunk_size: int
    uploaded_chunks: int = 0
    uploaded_rows: int = 0
    completed: bool = False


class ChunkedUploadManager:
    """Manage large file uploads in chunks with resume capability."""

    def __init__(
        self,
        store: UploadedDataStore,
        metadata_dir: Optional[Path | str] = None,
        *,
        initial_chunk_size: int = DEFAULT_CHUNK_SIZE,
        retry_manager_cls: type[ConnectionRetryManager] = ConnectionRetryManager,
    ) -> None:
        self.store = store
        self.metadata_dir = Path(metadata_dir or "temp/upload_metadata")
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.initial_chunk_size = initial_chunk_size
        self.min_chunk_size = 1000
        self.max_chunk_size = DataProcessingLimits.MAX_CHUNK_SIZE
        self.retry_config = RetryConfig(max_attempts=3, base_delay=0.2, jitter=False)
        self._retry_manager_cls = retry_manager_cls

    # ------------------------------------------------------------------
    def _metadata_path(self, filename: str) -> Path:
        return self.metadata_dir / f"{Path(filename).name}.json"

    def _load_metadata(self, filename: str) -> Optional[UploadMetadata]:
        path = self._metadata_path(filename)
        if path.exists():
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            return UploadMetadata(**data)
        return None

    def _save_metadata(self, meta: UploadMetadata) -> None:
        path = self._metadata_path(meta.filename)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(asdict(meta), fh, indent=2)

    @staticmethod
    def _count_rows(path: Path) -> int:
        with open(path, "rb") as fh:
            return max(sum(1 for _ in fh) - 1, 0)

    def _adjust_chunk_size(self, size: int, elapsed: float) -> int:
        if elapsed < 0.5:
            size = min(size * 2, self.max_chunk_size)
        elif elapsed > 2:
            size = max(int(size / 2), self.min_chunk_size)
        return size

    def _persist_chunk(self, name: str, df: pd.DataFrame) -> None:
        def _save() -> None:
            self.store.add_file(name, df)

        self._retry_manager_cls(self.retry_config).run_with_retry(_save)

    # ------------------------------------------------------------------
    def upload_file(self, file_path: str | Path, *, encoding: str = "utf-8") -> None:
        """Upload a file in chunks with adaptive sizing."""
        path = Path(file_path)
        meta = self._load_metadata(path.name)
        if meta is None:
            total_rows = self._count_rows(path)
            meta = UploadMetadata(
                filename=path.name,
                total_rows=total_rows,
                chunk_size=self.initial_chunk_size,
            )
            self._save_metadata(meta)
        if meta.completed:
            logger.info("Upload already completed for %s", path.name)
            return

        chunk_size = meta.chunk_size
        skip = meta.uploaded_rows
        reader = pd.read_csv(
            path,
            chunksize=chunk_size,
            encoding=encoding,
            skiprows=range(1, skip + 1) if skip else None,
        )
        idx = meta.uploaded_chunks
        for chunk in reader:
            start = time.monotonic()
            part_name = f"{meta.filename}.part{idx}"
            self._persist_chunk(part_name, chunk)
            elapsed = time.monotonic() - start
            chunk_size = self._adjust_chunk_size(chunk_size, elapsed)
            meta.uploaded_chunks = idx + 1
            meta.uploaded_rows += len(chunk)
            meta.chunk_size = chunk_size
            self._save_metadata(meta)
            idx += 1
        # Finalize upload by concatenating parts
        parts: list[pd.DataFrame] = []
        for i in range(meta.uploaded_chunks):
            part_name = f"{meta.filename}.part{i}"
            parts.append(self.store.load_dataframe(part_name))
        full_df = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
        self.store.add_file(meta.filename, full_df)
        meta.completed = True
        self._save_metadata(meta)

    def resume_upload(self, file_path: str | Path, *, encoding: str = "utf-8") -> None:
        """Resume an interrupted upload using stored metadata."""
        self.upload_file(file_path, encoding=encoding)

    def get_upload_progress(self, filename: str) -> float:
        """Return upload progress between 0 and 1."""
        meta = self._load_metadata(filename)
        if meta is None:
            return 0.0
        if meta.completed:
            return 1.0
        if meta.total_rows == 0:
            return 0.0
        progress = meta.uploaded_rows / meta.total_rows
        return max(0.0, min(progress, 1.0))


__all__ = ["ChunkedUploadManager", "UploadMetadata"]
