__all__ = [
    "analytics_controller",
    "interactive_charts",
    "anomaly_detection",
    "user_behavior",
    "access_trends",
    "security_patterns",
    "unique_patterns_analyzer",
    "security_metrics",
    "security_score_calculator",
    "db_interface",
    "file_processing_utils",
    "utils",
]

import logging


def initialize_security_callbacks() -> None:
    """Initialize security callbacks for the analytics package."""
    try:
        from security import SecurityModuleIntegration  # type: ignore
    except Exception:
        # Security integration not available
        return

    try:
        SecurityModuleIntegration.setup_analytics_callbacks()
    except Exception as exc:  # pragma: no cover - log and continue
        logging.getLogger(__name__).warning(
            "Failed to initialize security callbacks: %s", exc
        )


initialize_security_callbacks()
