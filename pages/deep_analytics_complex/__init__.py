"""Initialize the deep analytics page and expose callbacks."""

from analytics_core.callbacks.unified_callback_manager import CallbackManager
from security.unicode_security_processor import sanitize_dataframe
from services.data_processing.analytics_engine import (
    AI_SUGGESTIONS_AVAILABLE,
    analyze_data_with_service,
    analyze_data_with_service_safe,
    get_analysis_type_options,
    get_analytics_service_safe,
    get_data_source_options_safe,
    get_latest_uploaded_source_value,
    process_quality_analysis,
    process_quality_analysis_safe,
    process_suggests_analysis,
    process_suggests_analysis_safe,
)

from services.analytics_processing import (
    create_analysis_results_display,
    create_data_quality_display,
    create_suggests_display,
)
from .layout import (
    get_analysis_buttons_section,
    get_initial_message_safe,
    get_updated_button_group,
)

ANALYTICS_SERVICE_AVAILABLE = True
create_analysis_results_display_safe = create_analysis_results_display
create_data_quality_display_corrected = create_data_quality_display
create_limited_analysis_display = create_analysis_results_display
get_initial_message = get_initial_message_safe
from .callbacks import Callbacks, register_callbacks  # noqa: F401
from .layout import layout

__all__ = [
    "layout",
    "Callbacks",
    "register_callbacks",
    "ANALYTICS_SERVICE_AVAILABLE",
    "AI_SUGGESTIONS_AVAILABLE",
    "analyze_data_with_service",
    "analyze_data_with_service_safe",
    "create_analysis_results_display",
    "create_analysis_results_display_safe",
    "create_data_quality_display",
    "create_data_quality_display_corrected",
    "create_limited_analysis_display",
    "create_suggests_display",
    "get_analytics_service_safe",
    "get_analysis_buttons_section",
    "get_analysis_type_options",
    "get_data_source_options_safe",
    "get_initial_message",
    "get_initial_message_safe",
    "get_latest_uploaded_source_value",
    "get_updated_button_group",
    "process_quality_analysis",
    "process_quality_analysis_safe",
    "process_suggests_analysis",
    "process_suggests_analysis_safe",
    "sanitize_dataframe",
    "CallbackManager",
]

def __getattr__(name: str):
    if name.startswith(("create_", "get_")):
        def _stub(*args, **kwargs):
            return None
        return _stub
    raise AttributeError(f"module {__name__} has no attribute {name}")
