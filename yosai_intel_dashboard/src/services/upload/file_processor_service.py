import logging
from typing import Any, Callable, Dict, List

import pandas as pd

from yosai_intel_dashboard.src.core.interfaces.protocols import FileProcessorProtocol
from yosai_intel_dashboard.src.services.upload.protocols import UploadDataServiceProtocol, UploadStorageProtocol
from yosai_intel_dashboard.src.infrastructure.callbacks import CallbackType

logger = logging.getLogger(__name__)


class FileProcessor:
    """Process upload contents and persist dataframes."""

    def __init__(
        self,
        store: UploadStorageProtocol,
        processor: FileProcessorProtocol,
        data_service: UploadDataServiceProtocol,
    ) -> None:
        self.store = store
        self.processor = processor
        self.data_service = data_service

    def _combine_parts(self, parts: List[str]) -> str:
        if len(parts) == 1:
            return parts[0]
        prefix, first = parts[0].split(",", 1)
        data = first + "".join(p.split(",", 1)[1] for p in parts[1:])
        return f"{prefix},{data}"

    async def _process_one(
        self,
        filename: str,
        content: str,
        progress_cb: Callable[[int], None] | None,
    ) -> Dict[str, Any]:
        if progress_cb:
            self.processor.callbacks.register_callback(
                CallbackType.PROGRESS, progress_cb, component_id=filename
            )
        df = await self.processor.process_file(content, filename)
        mapping: Dict[str, str] = {}
        try:
            mapping = self.data_service.load_mapping(filename)
            if mapping:
                df = df.rename(columns=mapping)
        except Exception as exc:  # pragma: no cover - best effort
            logger.error("Failed to load mappings for %s: %s", filename, exc)
        self.store.add_file(filename, df)
        return {
            "df": df,
            "rows": len(df),
            "cols": len(df.columns),
            "column_names": df.columns.tolist(),
            "mapping": mapping,
        }

    async def process_files(
        self,
        file_parts: Dict[str, List[str]],
        task_progress: Callable[[int], None] | None = None,
    ) -> Dict[str, Dict[str, Any]]:
        results: Dict[str, Dict[str, Any]] = {}
        total = len(file_parts)
        processed = 0
        for name, parts in file_parts.items():
            content = self._combine_parts(parts)

            def _cb(pct: int) -> None:
                if task_progress:
                    overall = int(((processed + pct / 100) / total) * 100)
                    task_progress(overall)

            try:
                results[name] = await self._process_one(name, content, _cb)
            except Exception as exc:
                results[name] = {"error": str(exc)}
            processed += 1
            if task_progress:
                pct = int(processed / total * 100)
                task_progress(pct)
        return results
