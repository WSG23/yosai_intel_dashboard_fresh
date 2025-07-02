"""File upload page package."""
from dash.dependencies import Input, Output, State, ALL
from core.unified_callback_coordinator import UnifiedCallbackCoordinator
from analytics.controllers import UnifiedAnalyticsController
from utils.upload_store import uploaded_data_store as _uploaded_data_store

from .layout import layout
from .upload_handling import (
    build_success_alert,
    build_failure_alert,
    build_file_preview_component,
    get_uploaded_data,
    get_uploaded_filenames,
    clear_uploaded_data,
    get_file_info,
)
from .ai_device_classification import analyze_device_name_with_ai, auto_apply_learned_mappings
from .modal_dialogs import handle_modal_dialogs, apply_ai_suggestions
from .callbacks import Callbacks, register_callbacks, get_trigger_id

__all__ = [
    "layout",
    "Callbacks",
    "register_callbacks",
    "get_trigger_id",
    "build_success_alert",
    "build_failure_alert",
    "build_file_preview_component",
    "get_uploaded_data",
    "get_uploaded_filenames",
    "clear_uploaded_data",
    "get_file_info",
    "analyze_device_name_with_ai",
    "auto_apply_learned_mappings",
    "handle_modal_dialogs",
    "apply_ai_suggestions",
    "_uploaded_data_store",
]
