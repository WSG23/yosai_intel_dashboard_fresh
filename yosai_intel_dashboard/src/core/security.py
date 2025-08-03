# core/security.py
"""
Comprehensive security system for Yōsai Intel Dashboard
Implements Apple's security-by-design principles
"""
from __future__ import annotations

import hashlib
import logging
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

import validation.security_validator as security_validator_module
from monitoring.anomaly_detector import AnomalyDetector
from validation.security_validator import SecurityValidator
from yosai_intel_dashboard.src.core.base_model import BaseModel
from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import (
    dynamic_config,
)


# Import the high-level ``SecurityValidator`` used across the application.
# This module keeps no internal validation logic and instead delegates to
# :class:`~validation.security_validator.SecurityValidator` for sanitization tasks.
security_validator_module.redis_client = None

try:  # Optional during unit tests
    from yosai_intel_dashboard.src.core.domain.entities.access_events import (
        AccessEventModel,
    )
except Exception:  # pragma: no cover - model may be unavailable
    AccessEventModel = None

# Reuse a single validator instance for lightweight string sanitization across
# the application.  The validator implements the heavy lifting in
# ``validation.security_validator.SecurityValidator``; this helper simply
# delegates to it so callers don't need to instantiate or import the class
# directly.
_INPUT_VALIDATOR: SecurityValidator | None = None


def validate_user_input(value: str, field_name: str = "input") -> str:
    """Return a sanitized version of ``value``.

    Parameters
    ----------
    value:
        User supplied string to validate.
    field_name:
        Optional identifier used for logging context.

    Raises
    ------
    validation.security_validator.ValidationError
        If the underlying validator determines the value is unsafe.

    Returns
    -------
    str
        Sanitized representation suitable for downstream processing.
    """

    global _INPUT_VALIDATOR
    if _INPUT_VALIDATOR is None:
        # ``SecurityValidator`` optionally relies on a Redis client for rate
        # limiting.  During tests this client may not be configured, so ensure
        # the module has a ``redis_client`` attribute set to ``None`` before
        # instantiation to avoid ``NameError``.
        import validation.security_validator as _sv  # local import for patching

        if not hasattr(_sv, "redis_client"):
            _sv.redis_client = None  # type: ignore[attr-defined]
        _INPUT_VALIDATOR = _sv.SecurityValidator()
    result = _INPUT_VALIDATOR.validate_input(value, field_name)
    return result.get("sanitized", value)


class SecurityLevel(Enum):
    """Security threat levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationResult(Enum):
    """Input validation results"""

    VALID = "valid"
    INVALID = "invalid"
    SUSPICIOUS = "suspicious"
    MALICIOUS = "malicious"


@dataclass
class SecurityEvent:
    """Security event for logging and monitoring"""

    event_id: str
    timestamp: datetime
    event_type: str
    severity: SecurityLevel
    source_ip: Optional[str]
    user_id: Optional[str]
    details: Dict[str, Any]
    blocked: bool = False


class SecurityAuditor(BaseModel):
    """Security event logging and monitoring"""

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
        anomaly_detector: Optional[AnomalyDetector] = None,
    ) -> None:
        super().__init__(config, db, logger)
        self.events: List[SecurityEvent] = []
        self.max_events = 10000
        access_model = AccessEventModel(db) if (db and AccessEventModel) else None
        self.anomaly_detector = anomaly_detector or AnomalyDetector(access_model)
        self.anomaly_metrics: Dict[str, int] = self.anomaly_detector.get_metrics()

    def log_security_event(
        self,
        event_type: str,
        severity: SecurityLevel,
        details: Dict[str, Any],
        source_ip: Optional[str] = None,
        user_id: Optional[str] = None,
        blocked: bool = False,
    ) -> SecurityEvent:
        """Log a security event"""

        event = SecurityEvent(
            event_id=secrets.token_hex(8),
            timestamp=datetime.now(),
            event_type=event_type,
            severity=severity,
            source_ip=source_ip,
            user_id=user_id,
            details=details,
            blocked=blocked,
        )
        if self.anomaly_detector:
            score, flagged = self.anomaly_detector.score(user_id, source_ip)
            event.details["anomaly_score"] = score
            event.details["anomaly_flagged"] = flagged
            self.anomaly_metrics = self.anomaly_detector.get_metrics()
            if flagged:
                hint = "user exceeding normal rate; investigate credentials"
                event.details["remediation_hint"] = hint
                self.logger.warning(
                    f"Anomaly detected for user {user_id or 'unknown'} from "
                    f"{source_ip or 'unknown'}: {hint}"
                )

        self.events.append(event)

        # Limit stored events
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events :]

        # Log based on severity
        log_message = (
            f"Security Event [{event.event_id}]: {event_type} - {severity.value}"
        )
        if severity == SecurityLevel.CRITICAL:
            self.logger.critical(log_message)
        elif severity == SecurityLevel.HIGH:
            self.logger.error(log_message)
        elif severity == SecurityLevel.MEDIUM:
            self.logger.warning(log_message)
        else:
            self.logger.info(log_message)

        return event

    def get_security_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get security events summary"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_events = [e for e in self.events if e.timestamp >= cutoff]

        if not recent_events:
            return {"total_events": 0}

        # Group by severity
        by_severity = {}
        for severity in SecurityLevel:
            by_severity[severity.value] = len(
                [e for e in recent_events if e.severity == severity]
            )

        # Group by event type
        by_type = {}
        for event in recent_events:
            by_type[event.event_type] = by_type.get(event.event_type, 0) + 1

        # Get blocked events
        blocked_events = [e for e in recent_events if e.blocked]

        return {
            "total_events": len(recent_events),
            "by_severity": by_severity,
            "by_type": by_type,
            "blocked_events": len(blocked_events),
            "unique_ips": len(set(e.source_ip for e in recent_events if e.source_ip)),
            "high_severity_events": [
                {
                    "event_id": e.event_id,
                    "type": e.event_type,
                    "timestamp": e.timestamp,
                    "details": e.details,
                }
                for e in recent_events
                if e.severity in [SecurityLevel.HIGH, SecurityLevel.CRITICAL]
            ],
        }


class SecureHashManager:
    """Secure hashing for sensitive data"""

    @staticmethod
    def hash_password(password: str, salt: Optional[bytes] = None) -> Dict[str, str]:
        """Hash password with salt"""
        if salt is None:
            salt = secrets.token_bytes(dynamic_config.security.salt_bytes)

        # Use PBKDF2 with SHA256
        hash_bytes = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt, dynamic_config.security.pbkdf2_iterations
        )

        return {
            "hash": hash_bytes.hex(),
            "salt": salt.hex(),
            "algorithm": "pbkdf2_sha256",
            "iterations": dynamic_config.security.pbkdf2_iterations,
        }

    @staticmethod
    def verify_password(password: str, stored_hash: str, stored_salt: str) -> bool:
        """Verify password against stored hash"""
        salt = bytes.fromhex(stored_salt)
        hash_bytes = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt,
            dynamic_config.security.pbkdf2_iterations,
        )
        return hash_bytes.hex() == stored_hash

    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """Hash sensitive data for storage"""
        return hashlib.sha256(data.encode()).hexdigest()


# Global security instances
try:  # Allow initialization without optional dependencies
    security_validator = SecurityValidator()
except Exception:  # pragma: no cover

    class _FallbackValidator:
        def validate_input(
            self, value: str, field: str | None = None
        ) -> Dict[str, Any]:
            return {"valid": True, "sanitized": value}

    security_validator = _FallbackValidator()

rate_limiter = RateLimiter()
security_auditor = SecurityAuditor()


# Decorators for easy security integration
def validate_input_decorator(field_mapping: Dict[str, str] = None):
    """Decorator to validate function inputs"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Validate kwargs if field mapping provided
            if field_mapping:
                for param_name, field_name in field_mapping.items():
                    if param_name in kwargs:
                        try:
                            kwargs[param_name] = validate_user_input(
                                kwargs[param_name], field_name
                            )
                        except Exception as exc:
                            security_auditor.log_security_event(
                                "input_validation_failed",
                                SecurityLevel.HIGH,
                                {
                                    "function": func.__name__,
                                    "field": field_name,
                                    "issues": [str(exc)],
                                },
                            )
                            raise ValueError(
                                f"Invalid input for {field_name}: {exc}"  # noqa: EM102
                            )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def rate_limit_decorator(max_requests: int = 100, window_minutes: int = 1):
    """Decorator to apply rate limiting"""
    limiter = RateLimiter(max_requests, window_minutes)

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Use function name as identifier
            identifier = f"{func.__module__}.{func.__name__}"

            # Check rate limit
            result = limiter.is_allowed(identifier)
            if not result["allowed"]:
                security_auditor.log_security_event(
                    "rate_limit_exceeded",
                    SecurityLevel.MEDIUM,
                    {"function": func.__name__, "reason": result["reason"]},
                    blocked=True,
                )
                raise Exception(f"Rate limit exceeded: {result['reason']}")

            return func(*args, **kwargs)

        return wrapper

    return decorator


def initialize_validation_callbacks() -> None:
    """Set up request validation callbacks on import."""
    try:
        from security.validation_middleware import ValidationMiddleware
        from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import (  # noqa: E501
            TrulyUnifiedCallbacks,
        )
    except Exception:
        # Optional components may be missing in minimal environments
        return

    try:
        middleware = ValidationMiddleware()
        manager = TrulyUnifiedCallbacks()
        middleware.handle_registers(manager)
    except Exception as exc:  # pragma: no cover - log and continue
        logging.getLogger(__name__).warning(
            f"Failed to initialize validation callbacks: {exc}"
        )


initialize_validation_callbacks()
