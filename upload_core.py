"""Core upload processing helpers extracted from the Dash page."""
from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Tuple

import dash_bootstrap_components as dbc
from dash import html, no_update

from services.device_learning_service import get_device_learning_service
from services.task_queue import clear_task, create_task, get_status
from services.upload import (
    AISuggestionService,
    ChunkedUploadManager,
    ClientSideValidator,
    ModalService,
    UploadProcessingService,
    UploadQueueManager,
    get_trigger_id,
)
from upload_validator import UploadValidator
from utils.upload_store import uploaded_data_store as _uploaded_data_store

logger = logging.getLogger(__name__)


class UploadCore:
    """Container for upload related operations."""

    def __init__(self, store=_uploaded_data_store) -> None:
        self.store = store
        self.processing = UploadProcessingService(store)
        self.preview_processor = self.processing.async_processor
        self.ai = AISuggestionService()
        self.modal = ModalService()
        self.client_validator = ClientSideValidator()
        self.validator = UploadValidator()
        self.chunked = ChunkedUploadManager()
        self.queue = UploadQueueManager()

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
            res = self.validator.validate_file_upload(content)
            ok, msg = res.valid, res.message
            if not ok:
                alerts.append(self.processing.build_failure_alert(msg))
            else:
                valid_contents.append(content)
                valid_filenames.append(fname)
                self.chunked.start_file(fname)
                self.queue.add_file(fname)

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
        async_coro = self.processing.process_files(contents_list, filenames_list)
        task_id = create_task(async_coro)
        return task_id

    def reset_upload_progress(self, contents_list: List[str] | str) -> Tuple[int, str, bool]:
        if not contents_list:
            return 0, "0%", True
        return 0, "0%", False

    def update_progress_bar(self, _n: int, task_id: str) -> Tuple[int, str, Any]:
        status = get_status(task_id)
        progress = int(status.get("progress", 0))
        file_items = [
            html.Li(
                dbc.Progress(
                    value=self.chunked.get_progress(fname),
                    label=f"{fname} {self.chunked.get_progress(fname)}%",
                    striped=True,
                    animated=True,
                    id={"type": "file-progress", "name": fname},
                    **{"aria-label": f"Upload progress for {fname}"},
                )
            )
            for fname in self.queue.files
        ]
        return progress, f"{progress}%", file_items

    def finalize_upload_results(
        self, _n: int, task_id: str
    ) -> Tuple[Any, Any, Any, Any, Any, Any, Any, bool]:
        status = get_status(task_id)
        result = status.get("result")

        if status.get("done") and result is not None:
            clear_task(task_id)
            if isinstance(result, Exception):
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
                    "is_restricted": "is_restricted" in (special[i] if i < len(special) else []),
                    "confidence": 1.0,
                    "device_name": device,
                    "source": "user_confirmed",
                    "saved_at": datetime.now().isoformat(),
                }

            learning_service = get_device_learning_service()
            if not filename:
                raise ValueError("No filename provided in file_info")
            if not devices:
                raise ValueError("No devices found in file_info")

            _uploaded_data_store.wait_for_pending_saves()
            df = _uploaded_data_store.load_dataframe(filename)
            if df is None:
                raise ValueError(f"Data for '{filename}' could not be loaded")
            if df.empty:
                raise ValueError(f"DataFrame for '{filename}' is empty")

            learning_service.save_user_device_mappings(df, filename, user_mappings)
            from services.ai_mapping_store import ai_mapping_store
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
