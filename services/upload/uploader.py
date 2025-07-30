import base64
import logging
from typing import Any, Dict

from services.task_queue import create_task, get_status
from services.data_processing.async_file_processor import AsyncFileProcessor
from services.data_processing.file_handler import FileHandler
from utils.upload_store import UploadedDataStore, uploaded_data_store

logger = logging.getLogger(__name__)


class Uploader:
    """Validate uploaded files and persist them with progress tracking."""

    def __init__(
        self,
        store: UploadedDataStore = uploaded_data_store,
        handler: FileHandler | None = None,
        processor: AsyncFileProcessor | None = None,
    ) -> None:
        self.store = store
        self.handler = handler or FileHandler()
        self.processor = processor or AsyncFileProcessor()

    # ------------------------------------------------------------------
    def validate_and_store_file(self, contents: str, filename: str) -> str:
        """Validate ``contents`` and schedule processing for ``filename``."""
        if not contents or not filename:
            raise ValueError("No file provided")
        try:
            _, data = contents.split(",", 1)
        except Exception as exc:  # pragma: no cover - malformed input
            raise ValueError("Invalid contents") from exc
        file_bytes = base64.b64decode(data)
        result = self.handler.validate_file_upload(file_bytes)
        if not result.valid:
            raise ValueError(result.message or "invalid")

        async def _job(progress):
            df = await self.processor.process_file(
                contents,
                filename,
                progress_callback=lambda _f, pct: progress(pct),
            )
            self.store.add_file(filename, df)
            return {"rows": len(df), "columns": len(df.columns)}

        return create_task(_job)

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Return processing status for ``job_id``."""
        return get_status(job_id)


__all__ = ["Uploader"]
