# core/security.py
"""
Comprehensive security system for Yōsai Intel Dashboard
Implements Apple's security-by-design principles
"""
import hashlib
import logging
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from config.dynamic_config import dynamic_config
from core.base_model import BaseModel

# Import the high-level ``SecurityValidator`` used across the application.
# This module keeps no internal validation logic and instead delegates to
# :class:`~validation.security_validator.SecurityValidator` for sanitization tasks.
from validation.security_validator import SecurityValidator


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


class RateLimiter:
    """Rate limiting to prevent abuse"""

    def __init__(
        self,
        max_requests: int = dynamic_config.security.rate_limit_requests,
        window_minutes: int = dynamic_config.security.rate_limit_window_minutes,
    ):
        self.max_requests = max_requests
        self.window_seconds = window_minutes * 60
        self.requests: Dict[str, List[float]] = {}
        self.blocked_ips: Dict[str, float] = {}
        self.logger = logging.getLogger(__name__)

    def is_allowed(
        self, identifier: str, source_ip: Optional[str] = None
    ) -> Dict[str, Any]:
        """Check if request is allowed"""
        current_time = time.time()

        # Check if IP is blocked
        if source_ip and source_ip in self.blocked_ips:
            if current_time < self.blocked_ips[source_ip]:
                return {
                    "allowed": False,
                    "reason": "IP temporarily blocked",
                    "retry_after": self.blocked_ips[source_ip] - current_time,
                }
            else:
                # Unblock IP
                del self.blocked_ips[source_ip]

        # Initialize or clean old requests
        if identifier not in self.requests:
            self.requests[identifier] = []

        # Remove old requests outside the window
        cutoff_time = current_time - self.window_seconds
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier] if req_time > cutoff_time
        ]

        # Check if under limit
        if len(self.requests[identifier]) >= self.max_requests:
            # Block IP if provided
            if source_ip:
                self.blocked_ips[source_ip] = current_time + (self.window_seconds * 2)
                self.logger.warning(f"Rate limit exceeded, blocking IP: {source_ip}")

            return {
                "allowed": False,
                "reason": "Rate limit exceeded",
                "requests_in_window": len(self.requests[identifier]),
                "max_requests": self.max_requests,
                "window_seconds": self.window_seconds,
            }

        # Record this request
        self.requests[identifier].append(current_time)

        return {
            "allowed": True,
            "requests_in_window": len(self.requests[identifier]),
            "remaining": self.max_requests - len(self.requests[identifier]),
        }


class SecurityAuditor(BaseModel):
    """Security event logging and monitoring"""

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(config, db, logger)
        self.events: List[SecurityEvent] = []
        self.max_events = 10000

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
security_validator = SecurityValidator()
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
                        validation = security_validator.validate_input(
                            kwargs[param_name], field_name
                        )
                        if not validation["valid"]:
                            security_auditor.log_security_event(
                                "input_validation_failed",
                                validation["severity"],
                                {
                                    "function": func.__name__,
                                    "field": field_name,
                                    "issues": validation["issues"],
                                },
                            )
                            raise ValueError(
                                "Invalid input for "
                                f"{field_name}: {validation['issues']}"
                            )

                        # Use sanitized input
                        kwargs[param_name] = validation["sanitized"]

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
        from core.callbacks import TrulyUnifiedCallbacks
        from security.validation_middleware import ValidationMiddleware
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
