from __future__ import annotations

"""File upload page wrapping the reusable upload component."""

import logging
import time
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Tuple, Union

import pandas as pd
from dash.exceptions import PreventUpdate

try:
    from dash import dcc, html, no_update
except Exception:  # pragma: no cover - optional Dash dependency
    from types import SimpleNamespace
    dcc = SimpleNamespace()
    html = SimpleNamespace()
    no_update = None

if TYPE_CHECKING:
    from core.truly_unified_callbacks import TrulyUnifiedCallbacks

from analytics.controllers import UnifiedAnalyticsController
from config.config import get_analytics_config
from core.callback_registry import debounce
from core.dash_profile import profile_callback


def _get_max_display_rows() -> int:
    return get_analytics_config().max_display_rows or 10000


import dash_bootstrap_components as dbc

try:
    from dash.dependencies import ALL, Input, Output, State
except Exception:  # pragma: no cover - optional Dash dependency
    ALL = Input = Output = State = None

from components.column_verification import save_verified_mappings
from components.upload import ClientSideValidator as ErrorDisplayValidator

try:
    from components.upload.drag_drop_upload_area import DragDropUploadArea
except Exception:  # pragma: no cover - optional UI component
    DragDropUploadArea = lambda *a, **k: None
from config.dynamic_config import dynamic_config
from core.unicode_processor import safe_unicode_encode

try:
    from core.callback_controller import CallbackEvent
    from core.callback_manager import CallbackManager
except Exception:  # pragma: no cover - optional dependency for tests
    CallbackEvent = type(
        "CallbackEvent",
        (),
        {
            "FILE_UPLOAD_START": "FILE_UPLOAD_START",
            "FILE_UPLOAD_ERROR": "FILE_UPLOAD_ERROR",
        },
    )

    class CallbackManager:  # type: ignore
        def trigger(self, *_a, **_kw):
            pass


from services.device_learning_service import get_device_learning_service
from services.task_queue import clear_task, create_task, get_status

try:
    from services.upload import (
        AISuggestionService,
        ChunkedUploadManager,
        ModalService,
        UploadProcessingService,
        get_trigger_id,
        save_ai_training_data,
    )
except Exception:  # pragma: no cover - optional dependency for tests
    AISuggestionService = type("AISuggestionService", (), {})
    ModalService = type("ModalService", (), {})



from services.upload_data_service import (
    clear_uploaded_data as service_clear_uploaded_data,
)
from services.upload_data_service import get_file_info as service_get_file_info
from services.upload_data_service import get_uploaded_data as service_get_uploaded_data
from services.upload_data_service import (
    get_uploaded_filenames as service_get_uploaded_filenames,
)
from utils.upload_store import uploaded_data_store as _uploaded_data_store

logger = logging.getLogger(__name__)


def layout() -> html.Div:
    """
    Create the upload page layout using the fixed upload component.
    """
    from components.upload.drag_drop_upload_area_fixed import FileUploadComponent

    upload_component = FileUploadComponent("main-file-upload")

    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H1("File Upload", className="mb-4"),
                html.P(
                    "Upload your data files to begin analysis. "
                    "Supported formats: CSV, Excel (.xlsx, .xls), and JSON files.",
                    className="text-muted mb-4"
                ),

                # Upload component
                upload_component.render(),

                # Additional info
                dbc.Card([
                    dbc.CardHeader("Upload Guidelines"),
                    dbc.CardBody([
                        html.Ul([
                            html.Li("Maximum file size: 50MB"),
                            html.Li("Multiple files can be uploaded simultaneously"),
                            html.Li("CSV files should use UTF-8 encoding when possible"),
                            html.Li("Excel files (.xlsx, .xls) are fully supported"),
                            html.Li("JSON files will be parsed and validated")
                        ])
                    ])
                ], className="mt-4"),

                # Toast container for notifications
                html.Div(id="toast-container"),

                # Hidden stores for data
                dcc.Store(id="file-info-store"),
                dcc.Store(id="upload-progress-store")

            ], width=12)
        ])
    ], fluid=True)


def register_upload_callbacks(
    manager: "TrulyUnifiedCallbacks",
    controller=None,
) -> None:
    """
    Register upload callbacks using the manager.
    
    Args:
        manager: Unified callback manager
        controller: Optional analytics controller
    """
    try:
        # Import the fixed component
        from components.upload.drag_drop_upload_area_fixed import FileUploadComponent
        
        # Create upload component instance
        upload_component = FileUploadComponent("main-file-upload")
        
        # Register callbacks through the manager's app
        upload_component.register_callbacks(manager.app)
        
        logger.info("✅ Upload callbacks registered successfully")
        
    except Exception as e:
        logger.error(f"❌ Failed to register upload callbacks: {e}")
        raise


def register_enhanced_upload_callbacks(
    manager: "TrulyUnifiedCallbacks",
    controller=None,
) -> None:
    """Enhanced upload callbacks - alias for compatibility."""
    return register_upload_callbacks(manager, controller)


def register_callbacks(
    manager: "TrulyUnifiedCallbacks",
    controller=None,
) -> None:
    """General callback registration - alias for compatibility."""
    return register_upload_callbacks(manager, controller)


def get_uploaded_data() -> Dict[str, pd.DataFrame]:
    """Get all uploaded data."""
    return service_get_uploaded_data()


def get_uploaded_filenames() -> List[str]:
    """Get list of uploaded filenames."""
    return service_get_uploaded_filenames()


def clear_uploaded_data() -> None:
    """Clear all uploaded data."""
    service_clear_uploaded_data()


def get_file_info() -> Dict[str, Dict[str, Any]]:
    """Return metadata about uploaded files."""
    return service_get_file_info()


def check_upload_system_health() -> Dict[str, Any]:
    """Run basic diagnostics for the upload page."""

    errors: List[str] = []

    # Confirm the upload component can be constructed
    try:  # pragma: no cover - best effort
        DragDropUploadArea()
    except Exception as exc:
        errors.append(f"component_error: {exc}")

    # Ensure the Unicode helper works as expected
    try:
        safe_unicode_encode("health-check")
    except Exception as exc:  # pragma: no cover - best effort
        errors.append(f"unicode_error: {exc}")

    # Verify base64 decoding helper
    try:
        from services.data_processing.unified_file_validator import safe_decode_file

        result = safe_decode_file("data:text/plain;base64,aGVsbG8=")
        if result != b"hello":
            errors.append("base64_helper_invalid")
    except Exception as exc:  # pragma: no cover - best effort
        errors.append(f"base64_error: {exc}")

    status = "healthy" if not errors else "unhealthy"
    return {"status": status, "errors": errors}


class Callbacks:
    """Container object for upload page callbacks."""

    def __init__(self, deps: UploadDependencies | None = None):
        deps = deps or build_dependencies()
        self.processing = deps.processing
        self.preview_processor = deps.preview_processor
        self.ai = deps.ai
        self.modal = deps.modal
        self.client_validator = deps.error_display
        self.validator = deps.client_validator
        self.chunked = deps.chunked
        self.queue = deps.queue

    def highlight_upload_area(self, n_clicks):
        """Highlight upload area when 'upload more' is clicked."""
        if n_clicks:
            return "file-upload-area file-upload-area--highlight"
        return "file-upload-area"

    def display_client_validation(self, data):
        """Show validation errors generated in the browser."""
        if not data:
            return no_update
        alerts = self.client_validator.build_error_alerts(data)
        return alerts

    async def restore_upload_state(self, pathname: str):
        """Return stored upload details when revisiting the upload page."""

        if pathname != "/file-upload" or not _uploaded_data_store:
            return (
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
                no_update,
            )

        upload_results: List[Any] = []
        file_preview_components: List[Any] = []
        current_file_info: Dict[str, Any] = {}

        file_infos = _uploaded_data_store.get_file_info()

        for filename, info in file_infos.items():
            path = info.get("path") or str(_uploaded_data_store.get_file_path(filename))
            try:
                df_preview = await self.preview_processor.preview_from_parquet(
                    path, rows=_get_max_display_rows()
                )
            except Exception:
                df_preview = _uploaded_data_store.load_dataframe(filename).head(
                    _get_max_display_rows()
                )

            rows = info.get("rows", len(df_preview))
            cols = info.get("columns", len(df_preview.columns))

            upload_results.append(
                self.processing.build_success_alert(
                    filename,
                    rows,
                    cols,
                    prefix="Previously uploaded:",
                    processed=False,
                )
            )

            file_preview_components.append(
                self.processing.build_file_preview_component(df_preview, filename)
            )

            current_file_info = {
                "filename": filename,
                "rows": rows,
                "columns": cols,
                "path": path,
                "ai_suggestions": info.get("ai_suggestions", {}),
            }

        upload_nav = html.Div(
            [
                html.Hr(),
                html.H5("Ready to analyze?"),
                dbc.Button(
                    "🚀 Go to Analytics", href="/analytics", color="success", size="lg"
                ),
            ]
        )

        return (
            upload_results,
            file_preview_components,
            {},
            upload_nav,
            current_file_info,
            False,
            False,
        )

    def schedule_upload_task(
        self, contents_list: List[str] | str, filenames_list: List[str] | str
    ) -> str:
        """Schedule background processing of uploaded files."""



__all__ = [
    "layout",
    "register_upload_callbacks",
    "get_uploaded_data",
    "get_uploaded_filenames",
    "clear_uploaded_data",
    "get_file_info",
    "check_upload_system_health",
]
