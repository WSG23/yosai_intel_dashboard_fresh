"""Security patterns analysis subpackage."""

from analytics_core.callbacks.unified_callback_manager import (
    CallbackManager as SecurityCallbackController,
)
from security_callback_controller import (
    SecurityEvent,
    emit_security_event,
    security_callback_controller,
)

from .analyzer import (
    EnhancedSecurityAnalyzer,
    PaginatedAnalyzer,
    SecurityPatternsAnalyzer,
    create_security_analyzer,
)
from .config import SecurityPatternsConfig
from .data_prep import prepare_security_data
from .no_access_detection import detect_no_access
from .pattern_detection import (
    detect_after_hours_anomalies,
    detect_critical_door_risks,
    detect_pattern_threats,
    detect_rapid_attempts,
)
from .statistical_detection import (
    detect_failure_rate_anomalies,
    detect_frequency_anomalies,
    detect_statistical_threats,
)
from .types import ThreatIndicator

__all__ = [
    "SecurityPatternsAnalyzer",
    "create_security_analyzer",
    "EnhancedSecurityAnalyzer",
    "PaginatedAnalyzer",
    "SecurityCallbackController",
    "SecurityEvent",
    "security_callback_controller",
    "emit_security_event",
    "prepare_security_data",
    "detect_failure_rate_anomalies",
    "detect_frequency_anomalies",
    "detect_statistical_threats",
    "detect_pattern_threats",
    "detect_rapid_attempts",
    "detect_after_hours_anomalies",
    "detect_critical_door_risks",
    "detect_no_access",
    "ThreatIndicator",
    "SecurityPatternsConfig",
]


def setup_isolated_security_testing() -> None:
    """Prepare the :mod:`analytics.security_patterns` package for isolated tests.

    The concrete logic has not been implemented yet. Calling this helper makes
    it explicit that test specific setup is unavailable and raises a
    :class:`NotImplementedError`.
    """

    raise NotImplementedError(
        "setup_isolated_security_testing has not been implemented yet"
    )


__all__.append("setup_isolated_security_testing")
