"""Utility helpers for Yōsai Intel Dashboard."""

try:
    from .unicode_utils import safe_unicode_encode, handle_surrogate_characters
    from .unicode_processor import (
        sanitize_data_frame,
        clean_unicode_surrogates,
        process_large_csv_content,
    )
    from .unicode_handler import sanitize_unicode_input
    from .analysis_helpers import (
        build_ai_suggestions,
        extract_counts,
        extract_security_metrics,
        render_results_card,
        get_display_title,
    )
except Exception:  # pragma: no cover - fallback when processor unavailable
    from .unicode_handler import sanitize_unicode_input, handle_surrogate_characters
    from .unicode_processor import safe_unicode_encode, sanitize_data_frame, clean_unicode_surrogates, process_large_csv_content  # type: ignore
    from .analysis_helpers import (
        build_ai_suggestions,
        extract_counts,
        extract_security_metrics,
        render_results_card,
        get_display_title,
    )

__all__: list[str] = [
    "sanitize_unicode_input",
    "safe_unicode_encode",
    "handle_surrogate_characters",
    "sanitize_data_frame",
    "clean_unicode_surrogates",
    "process_large_csv_content",
    "build_ai_suggestions",
    "extract_counts",
    "extract_security_metrics",
    "render_results_card",
    "get_display_title",
]

