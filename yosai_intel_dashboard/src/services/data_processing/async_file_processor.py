#!/usr/bin/env python3
"""Asynchronous CSV processing helpers."""


from __future__ import annotations

import asyncio
import base64
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Tuple

import pandas as pd

from yosai_intel_dashboard.src.core.interfaces.protocols import FileProcessorProtocol
from yosai_intel_dashboard.src.core.interfaces import ConfigProviderProtocol
from yosai_intel_dashboard.src.services.rabbitmq_client import RabbitMQClient
from yosai_intel_dashboard.src.services.task_queue import create_task, get_status
from yosai_intel_dashboard.src.utils.memory_utils import check_memory_limit

from .file_processor import UnicodeFileProcessor


class AsyncFileProcessor(FileProcessorProtocol):
    """Read CSV files asynchronously in chunks with progress reporting."""

    def __init__(
        self,
        chunk_size: int | None = None,
        *,
        task_queue_url: str | None = None,
        config: ConfigProviderProtocol | None = None,
    ) -> None:
        analytics_cfg = getattr(config, "analytics", None) if config else None
        self.chunk_size = chunk_size or getattr(analytics_cfg, "chunk_size", 50000)
        self.max_memory_mb = getattr(analytics_cfg, "max_memory_mb", 1024)
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._queue: RabbitMQClient | None = None
        if task_queue_url:
            try:
                self._queue = RabbitMQClient(task_queue_url)
            except Exception as exc:  # pragma: no cover - connection optional
                self.logger.error("RabbitMQ connection failed: %s", exc)
                self._queue = None

    async def read_csv_chunks(
        self,
        file_path: str | Path,
        *,
        encoding: str = "utf-8",
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> AsyncIterator[pd.DataFrame]:
        path = Path(file_path)
        total_lines = await asyncio.to_thread(self._count_lines, path)
        processed = 0
        reader = pd.read_csv(path, chunksize=self.chunk_size, encoding=encoding)

        def _next_chunk() -> pd.DataFrame | None:
            try:
                return next(reader)
            except StopIteration:
                return None

        while True:
            chunk = await asyncio.to_thread(_next_chunk)
            if chunk is None:
                break
            check_memory_limit(self.max_memory_mb, self.logger)
            processed += len(chunk)
            if progress_callback and total_lines:
                pct = int(processed / total_lines * 100)
                pct = max(0, min(100, pct))
                try:
                    progress_callback(pct)
                except Exception:  # pragma: no cover - best effort
                    pass
            yield chunk
        if progress_callback:
            try:
                progress_callback(100)
            except Exception:  # pragma: no cover - best effort
                pass

    async def load_csv(
        self,
        file_path: str | Path,
        *,
        encoding: str = "utf-8",
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> pd.DataFrame:
        chunks: List[pd.DataFrame] = []
        async for chunk in self.read_csv_chunks(
            file_path, encoding=encoding, progress_callback=progress_callback
        ):
            chunks.append(chunk)
        return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()

    async def process_file(
        self,
        contents: str,
        filename: str,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> pd.DataFrame:
        """Decode ``contents`` and return a sanitized ``DataFrame``."""
        prefix, data = contents.split(",", 1)
        raw = base64.b64decode(data)

        suffix = Path(filename).suffix or ".tmp"
        fd, path_str = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        path = Path(path_str)
        await asyncio.to_thread(path.write_bytes, raw)

        def _cb(pct: int) -> None:
            if progress_callback:
                try:
                    progress_callback(filename, pct)
                except Exception:  # pragma: no cover - best effort
                    pass

        try:
            if filename.lower().endswith(".csv"):
                df = await self.load_csv(path, progress_callback=_cb)
            elif filename.lower().endswith((".xlsx", ".xls")):
                df = await asyncio.to_thread(pd.read_excel, path)
                df = UnicodeFileProcessor.sanitize_dataframe_unicode(df)
                _cb(100)
            elif filename.lower().endswith(".json"):
                df = await asyncio.to_thread(pd.read_json, path)
                df = UnicodeFileProcessor.sanitize_dataframe_unicode(df)
                _cb(100)
            else:
                raise ValueError(f"Unsupported file type: {filename}")
        finally:
            try:
                os.unlink(path)
            except Exception:  # pragma: no cover - cleanup best effort
                pass
        return df

    async def read_uploaded_file(
        self, contents: str, filename: str
    ) -> Tuple[pd.DataFrame, str]:
        """Read uploaded file handling both async and sync contexts."""
        try:
            asyncio.get_running_loop()
            df = await asyncio.create_task(self.process_file(contents, filename))
        except RuntimeError:  # pragma: no cover - run outside event loop
            df = asyncio.run(self.process_file(contents, filename))
        return df, ""

    def process_file_async(self, contents: str, filename: str) -> str:
        """Schedule ``process_file`` using RabbitMQ when available."""

        if self._queue:
            payload = {"contents": contents, "filename": filename}
            return self._queue.publish(
                "tasks", "process_file", payload, priority=0, delay_ms=0
            )

        async def _job(progress: Callable[[int], None]):
            df = await self.process_file(
                contents, filename, progress_callback=lambda _f, pct: progress(pct)
            )
            return {"rows": len(df), "columns": len(df.columns)}

        return create_task(_job)

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Return current status for ``job_id``."""
        if self._queue:
            # No status tracking yet for RabbitMQ tasks
            return {"progress": 0, "result": None, "done": False}
        return get_status(job_id)

    @staticmethod
    def _count_lines(path: Path) -> int:
        with open(path, "rb") as fh:
            return max(sum(1 for _ in fh) - 1, 0)


__all__ = ["AsyncFileProcessor"]
