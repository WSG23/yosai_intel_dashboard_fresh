"""Security patterns analysis subpackage."""

from .analyzer import (
    SecurityPatternsAnalyzer,
    create_security_analyzer,
    EnhancedSecurityAnalyzer,
)
from core.callback_manager import CallbackManager as SecurityCallbackController
from security_callback_controller import (
    SecurityEvent,
    security_callback_controller,
    emit_security_event,

)

from .data_prep import prepare_security_data
from .statistical_detection import (
    detect_failure_rate_anomalies,
    detect_frequency_anomalies,
    detect_statistical_threats,
)
from .pattern_detection import (
    detect_pattern_threats,
    detect_rapid_attempts,
    detect_after_hours_anomalies,
)
from .types import ThreatIndicator

__all__ = [
    "SecurityPatternsAnalyzer",
    "create_security_analyzer",
    "EnhancedSecurityAnalyzer",
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
    "ThreatIndicator",
]
