#!/usr/bin/env python3
"""
Complete File Upload Page - Missing piece for consolidation
Integrates with analytics system
"""
import logging
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

import pandas as pd
from dash import dcc, html
from dash.dash import no_update

if TYPE_CHECKING:
    from core.truly_unified_callbacks import TrulyUnifiedCallbacks

from analytics.controllers import UnifiedAnalyticsController
from config.config import get_analytics_config
from core.callback_registry import debounce
from core.dash_profile import profile_callback


def _get_max_display_rows() -> int:
    return get_analytics_config().max_display_rows or 10000
import dash_bootstrap_components as dbc
from dash.dependencies import ALL, Input, Output, State

from components.advanced_upload import DragDropUploadArea
from components.column_verification import save_verified_mappings
from components.upload import ClientSideValidator as ErrorDisplayValidator
from config.dynamic_config import dynamic_config
from services.device_learning_service import get_device_learning_service
from services.task_queue import clear_task, create_task, get_status
from services.upload import (
    AISuggestionService,
    ModalService,
    UploadProcessingService,
    get_trigger_id,
    save_ai_training_data,
)
from services.upload.validators import ClientSideValidator
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
from .layout import layout
from .callbacks import Callbacks, register_upload_callbacks, register_callbacks




def get_uploaded_data() -> Dict[str, pd.DataFrame]:
    """Get all uploaded data (for use by analytics)."""
    return service_get_uploaded_data()


def get_uploaded_filenames() -> List[str]:
    """Get list of uploaded filenames."""
    return service_get_uploaded_filenames()


def clear_uploaded_data():
    """Clear all uploaded data."""
    service_clear_uploaded_data()


def get_file_info() -> Dict[str, Dict[str, Any]]:
    """Get information about uploaded files."""
    return service_get_file_info()


def check_upload_system_health() -> Dict[str, Any]:
    """Monitor upload system health."""
    issues = []
    storage_dir = _uploaded_data_store.storage_dir

    if not storage_dir.exists():
        issues.append(f"Storage directory missing: {storage_dir}")

    try:
        test_file = storage_dir / "test.tmp"
        test_file.write_text("test")
        test_file.unlink()
    except Exception as e:
        issues.append(f"Cannot write to storage directory: {e}")

    pending = len(_uploaded_data_store._save_futures)
    if pending > 10:
        issues.append(f"Too many pending saves: {pending}")

    return {"healthy": len(issues) == 0, "issues": issues}




# Export functions for integration with other modules

__all__ = [
    "layout",
    "Callbacks",
    "get_uploaded_data",
    "get_uploaded_filenames",
    "clear_uploaded_data",
    "get_file_info",
    "check_upload_system_health",
    "save_ai_training_data",
    "register_upload_callbacks",
    "register_callbacks",
]

logger.info(f"\U0001f50d FILE_UPLOAD.PY LOADED - Callbacks should be registered")
