"""Core upload processing helpers extracted from the Dash page."""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Tuple

import dash_bootstrap_components as dbc
from dash import html, no_update

from services.interfaces import get_device_learning_service
from services.rabbitmq_client import RabbitMQClient
from services.task_queue import (
    TaskQueue,
    TaskQueueProtocol,
)
from services.upload import (
    AISuggestionService,
    ChunkedUploadManager,
    ClientSideValidator,
    ModalService,
    get_trigger_id,
)
from services.upload.protocols import (
    DeviceLearningServiceProtocol,
    UploadProcessingServiceProtocol,
    UploadStorageProtocol,
)
from services.upload.upload_queue_manager import UploadQueueManager
from services.upload.upload_core_helpers import (
    process_uploaded_files_helper,
    finalize_upload_results_helper,
    save_confirmed_device_mappings_helper,
)
from validation.security_validator import SecurityValidator

logger = logging.getLogger(__name__)


class UploadCore:
    """Container for upload related operations."""

    def __init__(
        self,
        processing: UploadProcessingServiceProtocol,
        learning_service: DeviceLearningServiceProtocol,
        store: UploadStorageProtocol,
        task_queue: TaskQueueProtocol | None = None,
        task_queue_url: str | None = None,
    ) -> None:
        self.store = store
        self.processing = processing
        self.learning_service = learning_service
        self.preview_processor = self.processing.async_processor
        self.ai = AISuggestionService()
        self.modal = ModalService()
        self.client_validator = ClientSideValidator()
        self.validator = SecurityValidator()
        self.chunked = ChunkedUploadManager()
        self.queue = UploadQueueManager()
        self.task_queue = task_queue or TaskQueue()
        self.rabbitmq: RabbitMQClient | None = None
        if task_queue_url:
            try:
                self.rabbitmq = RabbitMQClient(task_queue_url)
            except Exception as exc:  # pragma: no cover - optional queue
                logger.error("RabbitMQ connection failed: %s", exc)

    def highlight_upload_area(self, n_clicks):
        if n_clicks:
            return "file-upload-area file-upload-area--highlight"
        return "file-upload-area"

    def display_client_validation(self, data):
        if not data:
            return no_update
        alerts = self.client_validator.build_error_alerts(data)
        return alerts

    async def process_uploaded_files(
        self, contents_list: List[str] | str, filenames_list: List[str] | str
    ) -> Tuple[Any, Any, Any, Any, Any, Any, Any]:
        return await process_uploaded_files_helper(self, contents_list, filenames_list)

    def schedule_upload_task(
        self, contents_list: List[str] | str, filenames_list: List[str] | str
    ) -> str:
        if not contents_list:
            return ""
        if not isinstance(contents_list, list):
            contents_list = [contents_list]
        if not isinstance(filenames_list, list):
            filenames_list = [filenames_list]
        async_coro = self.processing.process_files(contents_list, filenames_list)
        if self.rabbitmq:
            payload = {"contents": contents_list, "filenames": filenames_list}
            return self.rabbitmq.publish(
                "tasks", "upload_process", payload, priority=0, delay_ms=0
            )
        task_id = self.task_queue.create_task(async_coro)
        return task_id

    def reset_upload_progress(
        self, contents_list: List[str] | str
    ) -> Tuple[int, str, bool]:
        if not contents_list:
            return 0, "0%", True
        return 0, "0%", False

    def update_progress_bar(self, _n: int, task_id: str) -> Tuple[int, str, Any]:
        if self.rabbitmq:
            progress = 0
        else:
            status = self.task_queue.get_status(task_id)
            progress = int(status.get("progress", 0))
        file_items = [
            html.Li(
                dbc.Progress(
                    value=self.chunked.get_progress(fname),
                    label=f"{fname} {self.chunked.get_progress(fname)}%",
                    striped=True,
                    animated=True,
                    id={"type": "file-progress", "name": fname},
                )
            )
            for fname in self.queue.files
        ]
        return progress, f"{progress}%", file_items

    def finalize_upload_results(
        self, _n: int, task_id: str
    ) -> Tuple[Any, Any, Any, Any, Any, Any, Any, bool]:
        return finalize_upload_results_helper(self, _n, task_id)

    def save_confirmed_device_mappings(
        self, confirm_clicks, floors, security, access, special, file_info
    ) -> Tuple[Any, Any, Any]:
        return save_confirmed_device_mappings_helper(
            self, confirm_clicks, floors, security, access, special, file_info
        )


__all__ = ["UploadCore"]
