"""Core upload processing helpers extracted from the Dash page."""

from __future__ import annotations

import base64
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Tuple

import dash_bootstrap_components as dbc
from dash import html, no_update

from yosai_intel_dashboard.src.core.interfaces.service_protocols import get_device_learning_service
from yosai_intel_dashboard.src.services.kafka_client import KafkaClient
from yosai_intel_dashboard.src.services.task_queue import (
    TaskQueue,
    TaskQueueProtocol,
)
from .ai import AISuggestionService
from .chunked_upload_manager import ChunkedUploadManager  # fixed circular import
from .validators import ClientSideValidator
from .modal import ModalService
from .helpers import get_trigger_id
from yosai_intel_dashboard.src.services.upload.protocols import (
    DeviceLearningServiceProtocol,
    UploadProcessingServiceProtocol,
    UploadStorageProtocol,
)
from yosai_intel_dashboard.src.services.upload.upload_queue_manager import UploadQueueManager
from validation.security_validator import SecurityValidator, ValidationError
from yosai_intel_dashboard.src.utils.sanitization import sanitize_filename
from yosai_intel_dashboard.src.core.security import validate_user_input


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
        # Validator used for file uploads; string inputs are sanitized via
        # ``validate_user_input`` helper from :mod:`core.security`.
        self.validator = SecurityValidator()
        self.chunked = ChunkedUploadManager()
        self.queue = UploadQueueManager()
        self.task_queue = task_queue or TaskQueue()
        self.kafka: KafkaClient | None = None
        if task_queue_url:
            try:
                self.kafka = KafkaClient(task_queue_url)
            except Exception as exc:  # pragma: no cover - optional queue
                logger.error("Kafka connection failed: %s", exc)

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
        if not contents_list:
            return (
                [],
                [],
                {},
                [],
                {},
                no_update,
                no_update,
            )

        if not isinstance(contents_list, list):
            contents_list = [contents_list]
            filenames_list = [filenames_list]

        valid_contents: list[str] = []
        valid_filenames: list[str] = []
        alerts: list[Any] = []
        for content, fname in zip(contents_list, filenames_list):
            try:
                data = base64.b64decode(content.split(",", 1)[1])
                sanitized_name = sanitize_filename(str(fname))
                self.validator.validate_file_upload(sanitized_name, data)
            except (ValidationError, ValueError) as exc:
                alerts.append(self.processing.build_failure_alert(str(exc)))
            except Exception as exc:  # pragma: no cover - unexpected decoding issues
                logger.error("Failed to validate %s: %s", fname, exc)
                alerts.append(self.processing.build_failure_alert("Invalid file data"))

            else:
                valid_contents.append(content)
                valid_filenames.append(sanitized_name)
                self.chunked.start_file(sanitized_name)
                self.queue.add_file(sanitized_name)

        if not valid_contents:
            return alerts, [], {}, [], {}, no_update, no_update

        result = await self.processing.process_files(valid_contents, valid_filenames)

        for fname in valid_filenames:
            self.chunked.finish_file(fname)
            self.queue.mark_complete(fname)

        result = list(result)
        result[0] = alerts + result[0]
        return tuple(result)

    def schedule_upload_task(
        self, contents_list: List[str] | str, filenames_list: List[str] | str
    ) -> str:
        if not contents_list:
            return ""
        if not isinstance(contents_list, list):
            contents_list = [contents_list]
        if not isinstance(filenames_list, list):
            filenames_list = [filenames_list]
        filenames_list = [sanitize_filename(str(f)) for f in filenames_list]
        async_coro = self.processing.process_files(contents_list, filenames_list)
        if self.kafka:
            payload = {"contents": contents_list, "filenames": filenames_list}
            return self.kafka.publish(
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
        task_id = validate_user_input(str(task_id), "task_id")
        if self.kafka:
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
        task_id = validate_user_input(str(task_id), "task_id")
        if self.kafka:
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )
        status = self.task_queue.get_status(task_id)
        result = status.get("result")

        if status.get("done") and result is not None:
            self.task_queue.clear_task(task_id)
            if not isinstance(result, Exception):
                try:
                    from yosai_intel_dashboard.src.components.simple_device_mapping import (
                        generate_ai_device_defaults,
                    )

                    for fname in self.store.get_filenames():
                        df = self.store.load_dataframe(fname)
                        if df is not None and not df.empty:
                            generate_ai_device_defaults(df, "auto")
                except Exception as exc:  # pragma: no cover - best effort
                    logger.error("Failed to generate AI defaults: %s", exc)
            else:
                result = (
                    [self.processing.build_failure_alert(str(result))],
                    [],
                    {},
                    [],
                    {},
                    no_update,
                    no_update,
                )
            return (*result, True)

        return (
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
            no_update,
        )

    def save_confirmed_device_mappings(
        self, confirm_clicks, floors, security, access, special, file_info
    ) -> Tuple[Any, Any, Any]:
        if not confirm_clicks or not file_info:
            return no_update, no_update, no_update
        try:
            devices = file_info.get("devices", [])
            filename = file_info.get("filename", "")

            user_mappings = {}
            for i, device in enumerate(devices):
                user_mappings[device] = {
                    "floor_number": floors[i] if i < len(floors) else 1,
                    "security_level": security[i] if i < len(security) else 5,
                    "is_entry": "entry" in (access[i] if i < len(access) else []),
                    "is_exit": "exit" in (access[i] if i < len(access) else []),
                    "is_restricted": "is_restricted"
                    in (special[i] if i < len(special) else []),
                    "confidence": 1.0,
                    "device_name": device,
                    "source": "user_confirmed",
                    "saved_at": datetime.now().isoformat(),
                }

            learning_service = self.learning_service
            if not filename:
                raise ValueError("No filename provided in file_info")
            if not devices:
                raise ValueError("No devices found in file_info")

            self.store.wait_for_pending_saves()
            df = self.store.load_dataframe(filename)
            if df is None:
                raise ValueError(f"Data for '{filename}' could not be loaded")
            if df.empty:
                raise ValueError(f"DataFrame for '{filename}' is empty")

            learning_service.save_user_device_mappings(df, filename, user_mappings)
            from yosai_intel_dashboard.src.services.ai_mapping_store import ai_mapping_store

            ai_mapping_store.update(user_mappings)

            success_alert = dbc.Toast(
                "✅ Device mappings saved to database!",
                header="Confirmed & Saved",
                is_open=True,
                dismissable=True,
                duration=3000,
            )
            return success_alert, False, False
        except Exception as e:  # pragma: no cover - robustness
            logger.error("Error saving device mappings: %s", e)
            error_alert = dbc.Toast(
                f"❌ Error saving mappings: {e}",
                header="Error",
                is_open=True,
                dismissable=True,
                duration=8000,
            )
            return error_alert, no_update, no_update


__all__ = ["UploadCore"]
