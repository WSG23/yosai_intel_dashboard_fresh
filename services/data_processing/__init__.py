"""Data processing utilities."""

from .file_handler import FileHandler, process_file_simple, FileProcessingError

import logging
import pandas as pd
from typing import Any, Dict

logger = logging.getLogger(__name__)


def process_file(contents: str, filename: str) -> Dict[str, Any]:
    """Decode ``contents`` and return a DataFrame with status info."""

    handler = FileHandler()
    try:
        df = handler.process_base64_contents(contents, filename)
        return {"success": True, "data": df}
    except Exception as exc:  # pragma: no cover - best effort
        logger.error("process_file failed: %s", exc)
        return {"success": False, "error": str(exc), "data": pd.DataFrame()}

# Analytics helpers are intentionally loaded lazily in environments where the
# full analytics stack is unavailable. ``AI_SUGGESTIONS_AVAILABLE`` defaults to
# ``False`` and can be overridden by calling :func:`load_analytics_helpers`.
AI_SUGGESTIONS_AVAILABLE = False


def load_analytics_helpers() -> None:  # pragma: no cover - optional
    """Populate module globals with analytics helper functions."""
    from .analytics_engine import (
        AI_SUGGESTIONS_AVAILABLE as _AI,
        get_analytics_service_safe,
        get_data_source_options_safe,
        get_latest_uploaded_source_value,
        get_analysis_type_options,
        clean_analysis_data_unicode,
        get_ai_suggestions_for_file,
        process_suggests_analysis,
        process_quality_analysis,
        analyze_data_with_service,
        process_suggests_analysis_safe,
        process_quality_analysis_safe,
        analyze_data_with_service_safe,
    )

    globals().update(
        AI_SUGGESTIONS_AVAILABLE=_AI,
        get_analytics_service_safe=get_analytics_service_safe,
        get_data_source_options_safe=get_data_source_options_safe,
        get_latest_uploaded_source_value=get_latest_uploaded_source_value,
        get_analysis_type_options=get_analysis_type_options,
        clean_analysis_data_unicode=clean_analysis_data_unicode,
        get_ai_suggestions_for_file=get_ai_suggestions_for_file,
        process_suggests_analysis=process_suggests_analysis,
        process_quality_analysis=process_quality_analysis,
        analyze_data_with_service=analyze_data_with_service,
        process_suggests_analysis_safe=process_suggests_analysis_safe,
        process_quality_analysis_safe=process_quality_analysis_safe,
        analyze_data_with_service_safe=analyze_data_with_service_safe,
    )


__all__ = [
    "FileHandler",
    "process_file",
    "process_file_simple",
    "FileProcessingError",
]
