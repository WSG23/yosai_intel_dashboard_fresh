"""Data processing utilities."""

try:  # pragma: no cover - optional dependency
    from .async_file_processor import AsyncFileProcessor
except Exception:  # pragma: no cover - best effort
    AsyncFileProcessor = None  # type: ignore
from .base_file_processor import BaseFileProcessor
from .file_handler import FileHandler, process_file_simple

# ``FileProcessor`` was removed in favor of ``UnicodeFileProcessor``.  Import
# the new class here and optionally expose it under the old name for backward
# compatibility.
from .file_processor import UnicodeFileProcessor

# Provide the legacy name ``FileProcessor`` for callers that still import it
# from ``services.data_processing``.
FileProcessor = UnicodeFileProcessor
from .core.exceptions import (
    FileFormatError,
    FileProcessingError,
    FileSecurityError,
    FileSizeError,
    FileValidationError,
)

# Analytics helpers are intentionally loaded lazily in environments where the
# full analytics stack is unavailable. ``AI_SUGGESTIONS_AVAILABLE`` defaults to
# ``False`` and can be overridden by calling :func:`load_analytics_helpers`.
AI_SUGGESTIONS_AVAILABLE = False


def load_analytics_helpers() -> None:  # pragma: no cover - optional
    """Populate module globals with analytics helper functions."""
    from .analytics_engine import AI_SUGGESTIONS_AVAILABLE as _AI
    from .analytics_engine import (
        analyze_data_with_service,
        analyze_data_with_service_safe,
        clean_analysis_data_unicode,
        get_ai_suggestions_for_file,
        get_analysis_type_options,
        get_data_source_options_safe,
        get_latest_uploaded_source_value,
        process_quality_analysis,
        process_quality_analysis_safe,
        process_suggests_analysis,
        process_suggests_analysis_safe,
    )

    globals().update(
        AI_SUGGESTIONS_AVAILABLE=_AI,
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
    "AsyncFileProcessor",
    "process_file_simple",
    "FileProcessingError",
    "FileValidationError",
    "FileFormatError",
    "FileSizeError",
    "FileSecurityError",
    "BaseFileProcessor",
]
