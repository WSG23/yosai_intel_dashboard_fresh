from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, List, Tuple

import dash_bootstrap_components as dbc
from dash import html, no_update

logger = logging.getLogger(__name__)


async def process_uploaded_files_helper(core: "UploadCore", contents_list: List[str] | str, filenames_list: List[str] | str) -> Tuple[Any, Any, Any, Any, Any, Any, Any]:
    """Validate and process uploaded files."""
    if not contents_list:
        return ([], [], {}, [], {}, no_update, no_update)

    if not isinstance(contents_list, list):
        contents_list = [contents_list]
        filenames_list = [filenames_list]

    valid_contents: list[str] = []
    valid_filenames: list[str] = []
    alerts: list[Any] = []
    for content, fname in zip(contents_list, filenames_list):
        res = core.validator.validate_file_upload(content)
        ok, msg = res.valid, res.message
        if not ok:
            alerts.append(core.processing.build_failure_alert(msg))
        else:
            valid_contents.append(content)
            valid_filenames.append(fname)
            core.chunked.start_file(fname)
            core.queue.add_file(fname)

    if not valid_contents:
        return alerts, [], {}, [], {}, no_update, no_update

    result = await core.processing.process_files(valid_contents, valid_filenames)

    for fname in valid_filenames:
        core.chunked.finish_file(fname)
        core.queue.mark_complete(fname)

    result = list(result)
    result[0] = alerts + result[0]
    return tuple(result)


def finalize_upload_results_helper(core: "UploadCore", _n: int, task_id: str) -> Tuple[Any, Any, Any, Any, Any, Any, Any, bool]:
    """Return result of async upload task when complete."""
    if core.rabbitmq:
        return (no_update,) * 8
    status = core.task_queue.get_status(task_id)
    result = status.get("result")

    if status.get("done") and result is not None:
        core.task_queue.clear_task(task_id)
        if not isinstance(result, Exception):
            try:
                from components.simple_device_mapping import generate_ai_device_defaults

                for fname in core.store.get_filenames():
                    df = core.store.load_dataframe(fname)
                    if df is not None and not df.empty:
                        generate_ai_device_defaults(df, "auto")
            except Exception as exc:  # pragma: no cover - best effort
                logger.error("Failed to generate AI defaults: %s", exc)
        else:
            result = (
                [core.processing.build_failure_alert(str(result))],
                [],
                {},
                [],
                {},
                no_update,
                no_update,
            )
        return (*result, True)

    return (no_update,) * 8


def save_confirmed_device_mappings_helper(core: "UploadCore", confirm_clicks, floors, security, access, special, file_info) -> Tuple[Any, Any, Any]:
    """Persist user confirmed mappings."""
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

        learning_service = core.learning_service
        if not filename:
            raise ValueError("No filename provided in file_info")
        if not devices:
            raise ValueError("No devices found in file_info")

        core.store.wait_for_pending_saves()
        df = core.store.load_dataframe(filename)
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


__all__ = [
    "process_uploaded_files_helper",
    "finalize_upload_results_helper",
    "save_confirmed_device_mappings_helper",
]
