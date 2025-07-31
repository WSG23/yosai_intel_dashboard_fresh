import asyncio
import json
import logging
import random
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Awaitable, Callable, Optional, TypeVar

import pandas as pd

from config.connection_retry import RetryConfig
from config.constants import DEFAULT_CHUNK_SIZE, DataProcessingLimits
from config.database_exceptions import ConnectionRetryExhausted
from yosai_intel_dashboard.src.utils.upload_store import UploadedDataStore

logger = logging.getLogger(__name__)

T = TypeVar("T")


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
    """Manage large file uploads asynchronously with resume capability."""

    def __init__(
        self,
        store: UploadedDataStore,
        metadata_dir: Optional[Path | str] = None,
        *,
        initial_chunk_size: int = DEFAULT_CHUNK_SIZE,
        bandwidth_limit: float | None = None,
    ) -> None:
        self.store = store
        self.metadata_dir = Path(metadata_dir or "temp/upload_metadata")
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        self.initial_chunk_size = initial_chunk_size
        self.bandwidth_limit = bandwidth_limit  # bytes per second
        self.min_chunk_size = 1000
        self.max_chunk_size = DataProcessingLimits.MAX_CHUNK_SIZE
        self.retry_config = RetryConfig(max_attempts=3, base_delay=0.2, jitter=False)

    # ------------------------------------------------------------------
    def _metadata_path(self, filename: str) -> Path:
        return self.metadata_dir / f"{Path(filename).name}.json"

    async def _load_metadata(self, filename: str) -> Optional[UploadMetadata]:
        path = self._metadata_path(filename)
        if await asyncio.to_thread(path.exists):
            data = await asyncio.to_thread(json.loads, path.read_text(encoding="utf-8"))
            return UploadMetadata(**data)
        return None

    async def _save_metadata(self, meta: UploadMetadata) -> None:
        path = self._metadata_path(meta.filename)
        dump = json.dumps(asdict(meta), indent=2)
        await asyncio.to_thread(path.write_text, dump, encoding="utf-8")

    async def _count_rows(self, path: Path) -> int:
        def _count() -> int:
            with open(path, "rb") as fh:
                return max(sum(1 for _ in fh) - 1, 0)

        return await asyncio.to_thread(_count)

    def _adjust_chunk_size(self, size: int, elapsed: float) -> int:
        if elapsed < 0.5:
            size = min(size * 2, self.max_chunk_size)
        elif elapsed > 2:
            size = max(int(size / 2), self.min_chunk_size)
        return size

    async def _run_with_retry(self, func: Callable[[], Awaitable[T]]) -> T:
        attempt = 1
        while True:
            try:
                return await func()
            except Exception as exc:
                if attempt >= self.retry_config.max_attempts:
                    raise ConnectionRetryExhausted(
                        "maximum retry attempts reached"
                    ) from exc
                delay = self.retry_config.base_delay * (
                    self.retry_config.backoff_factor ** (attempt - 1)
                )
                if self.retry_config.jitter:
                    delay += random.uniform(0, self.retry_config.base_delay)
                delay = min(delay, self.retry_config.max_delay)
                await asyncio.sleep(delay)
                attempt += 1

    async def _persist_chunk(self, name: str, df: pd.DataFrame) -> None:
        async def _save() -> None:
            await asyncio.to_thread(self.store.add_file, name, df)

        await self._run_with_retry(_save)

    async def upload_file(
        self, file_path: str | Path, *, encoding: str = "utf-8"
    ) -> None:
        """Upload a file in chunks with adaptive sizing."""
        path = Path(file_path)
        meta = await self._load_metadata(path.name)
        if meta is None:
            total_rows = await self._count_rows(path)
            meta = UploadMetadata(
                filename=path.name,
                total_rows=total_rows,
                chunk_size=self.initial_chunk_size,
            )
            await self._save_metadata(meta)
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

        def _next_chunk() -> pd.DataFrame | None:
            try:
                return next(reader)
            except StopIteration:
                return None

        idx = meta.uploaded_chunks
        while True:
            chunk = await asyncio.to_thread(_next_chunk)
            if chunk is None:
                break
            start = time.monotonic()
            part_name = f"{meta.filename}.part{idx}"
            await self._persist_chunk(part_name, chunk)
            elapsed = time.monotonic() - start
            if self.bandwidth_limit:
                chunk_bytes = int(chunk.memory_usage(deep=True).sum())
                min_time = chunk_bytes / self.bandwidth_limit
                if elapsed < min_time:
                    await asyncio.sleep(min_time - elapsed)
            chunk_size = self._adjust_chunk_size(chunk_size, elapsed)
            meta.uploaded_chunks = idx + 1
            meta.uploaded_rows += len(chunk)
            meta.chunk_size = chunk_size
            await self._save_metadata(meta)
            idx += 1

        parts = []
        for i in range(meta.uploaded_chunks):
            part_name = f"{meta.filename}.part{i}"
            df_part = await asyncio.to_thread(self.store.load_dataframe, part_name)
            parts.append(df_part)
        full_df = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
        await asyncio.to_thread(self.store.add_file, meta.filename, full_df)
        meta.completed = True
        await self._save_metadata(meta)

    async def resume_upload(
        self, file_path: str | Path, *, encoding: str = "utf-8"
    ) -> None:
        """Resume an interrupted upload using stored metadata."""
        await self.upload_file(file_path, encoding=encoding)

    async def get_upload_progress(self, filename: str) -> float:
        """Return upload progress between 0 and 1."""
        meta = await self._load_metadata(filename)
        if meta is None:
            return 0.0
        if meta.completed:
            return 1.0
        if meta.total_rows == 0:
            return 0.0
        progress = meta.uploaded_rows / meta.total_rows
        return max(0.0, min(progress, 1.0))


__all__ = ["ChunkedUploadManager", "UploadMetadata"]
