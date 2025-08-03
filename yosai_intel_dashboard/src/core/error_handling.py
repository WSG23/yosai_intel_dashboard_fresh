# core/error_handling.py
"""
Comprehensive error handling system with Apple-style resilience patterns
"""
from __future__ import annotations

import functools
import logging
import time
from bisect import bisect_left
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from prometheus_client import REGISTRY, Counter
from prometheus_client.core import CollectorRegistry

from shared.errors.types import ErrorCode

from .base_model import BaseModel
from .exceptions import YosaiBaseException

# Counter tracking circuit breaker state transitions. When the metric already
# exists in the default registry (e.g. during test re-imports) we create the
# counter in an isolated registry to avoid duplicate registration errors.
if "circuit_breaker_state_transitions_total" not in REGISTRY._names_to_collectors:
    circuit_breaker_state = Counter(
        "circuit_breaker_state_transitions_total",
        "Count of circuit breaker state transitions",
        ["name", "state"],
    )
else:
    circuit_breaker_state = Counter(
        "circuit_breaker_state_transitions_total",
        "Count of circuit breaker state transitions",
        ["name", "state"],
        registry=CollectorRegistry(),
    )


class ErrorSeverity(Enum):
    """Error severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for better classification"""

    DATABASE = "database"
    FILE_PROCESSING = "file_processing"
    AUTHENTICATION = "authentication"
    ANALYTICS = "analytics"
    CONFIGURATION = "configuration"
    EXTERNAL_API = "external_api"
    USER_INPUT = "user_input"


@dataclass
class ErrorContext:
    """Rich error context for better debugging"""

    error_id: str
    timestamp: datetime
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: Dict[str, Any]
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    service: Optional[str] = None
    operation: Optional[str] = None
    stack_trace: Optional[str] = None


class YosaiError(YosaiBaseException):
    """Base exception class for all Yōsai-specific errors with extra context."""

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.ANALYTICS,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        details: Dict[str, Any] = None,
        error_code: ErrorCode = ErrorCode.INTERNAL,
    ) -> None:
        super().__init__(message, details, error_code)
        self.category = category
        self.severity = severity
        self.timestamp = datetime.now()


class CircuitBreakerError(YosaiError):
    """Raised when a circuit breaker is open."""

    def __init__(self, message: str, details: Dict[str, Any] | None = None) -> None:
        super().__init__(
            message,
            ErrorCategory.EXTERNAL_API,
            ErrorSeverity.HIGH,
            details,
        )


class ErrorHandler(BaseModel):
    """Centralized error handling with Apple-style patterns"""

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(config, db, logger)
        self.error_history: List[ErrorContext] = []
        self.max_history = 1000

    def handle_error(
        self,
        error: Exception,
        category: ErrorCategory = ErrorCategory.ANALYTICS,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        context: Dict[str, Any] = None,
    ) -> ErrorContext:
        """Handle an error with proper logging and tracking"""
        ctx: Dict[str, Any] = dict(context or {})
        service = ctx.pop("service", None)
        operation = ctx.pop("operation", None)
        user_id = ctx.pop("user_id", None)
        request_id = ctx.pop("request_id", None)

        error_context = ErrorContext(
            error_id=f"ERR_{int(time.time())}_{id(error)}",
            timestamp=datetime.now(),
            category=category,
            severity=severity,
            message=str(error),
            details=ctx,
            user_id=user_id,
            request_id=request_id,
            service=service,
            operation=operation,
            stack_trace=None,  # Could add traceback if needed
        )

        # Log based on severity
        if severity == ErrorSeverity.CRITICAL:
            self.logger.critical(
                f"CRITICAL ERROR [{error_context.error_id}]: {error_context.message}"
            )
        elif severity == ErrorSeverity.HIGH:
            self.logger.error(
                f"ERROR [{error_context.error_id}]: {error_context.message}"
            )
        elif severity == ErrorSeverity.MEDIUM:
            self.logger.warning(
                f"WARNING [{error_context.error_id}]: {error_context.message}"
            )
        else:
            self.logger.info(
                f"INFO [{error_context.error_id}]: {error_context.message}"
            )

        # Store in history
        self._add_to_history(error_context)

        return error_context

    def _add_to_history(self, error_context: ErrorContext) -> None:
        """Add error to history with size limit"""
        self.error_history.append(error_context)
        if len(self.error_history) > self.max_history:
            self.error_history.pop(0)

    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        timestamps = [e.timestamp for e in self.error_history]
        idx = bisect_left(timestamps, cutoff)
        recent_errors = self.error_history[idx:]

        return {
            "total_errors": len(recent_errors),
            "by_category": self._group_by_category(recent_errors),
            "by_severity": self._group_by_severity(recent_errors),
            "critical_errors": [
                e for e in recent_errors if e.severity == ErrorSeverity.CRITICAL
            ],
        }

    def _group_by_category(self, errors: List[ErrorContext]) -> Dict[str, int]:
        """Group errors by category"""
        result = {}
        for error in errors:
            category = error.category.value
            result[category] = result.get(category, 0) + 1
        return result

    def _group_by_severity(self, errors: List[ErrorContext]) -> Dict[str, int]:
        """Group errors by severity"""
        result = {}
        for error in errors:
            severity = error.severity.value
            result[severity] = result.get(severity, 0) + 1
        return result


# Global error handler instance
error_handler = ErrorHandler()


def with_error_handling(
    category: ErrorCategory = ErrorCategory.ANALYTICS,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    reraise: bool = False,
):
    """Decorator for automatic error handling"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                error_handler.handle_error(
                    e,
                    category=category,
                    severity=severity,
                    context={
                        "function": func.__name__,
                        "args": str(args)[:200],  # Limit size
                        "kwargs": str(kwargs)[:200],
                    },
                )

                if reraise:
                    raise

                # Return safe default based on function return type
                return None

        return wrapper

    return decorator


def with_async_error_handling(
    category: ErrorCategory = ErrorCategory.ANALYTICS,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    reraise: bool = False,
):
    """Decorator for async error handling"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                error_handler.handle_error(
                    e,
                    category=category,
                    severity=severity,
                    context={
                        "function": func.__name__,
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200],
                    },
                )

                if reraise:
                    raise

                return None

        return wrapper

    return decorator


def handle_errors(
    service: str,
    operation: str,
    *,
    category: ErrorCategory = ErrorCategory.ANALYTICS,
    severity: ErrorSeverity = ErrorSeverity.MEDIUM,
    reraise: bool = False,
) -> Callable[[Callable], Callable]:
    """Decorator to handle errors with rich context."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                user_id = None
                request_id = None
                try:
                    from flask import g, has_request_context

                    if has_request_context():
                        user_id = getattr(g, "user_id", None) or getattr(
                            g, "current_user_id", None
                        )
                        request_id = getattr(g, "request_id", None)
                except Exception:
                    pass

                error_handler.handle_error(
                    exc,
                    category=category,
                    severity=severity,
                    context={
                        "service": service,
                        "operation": operation,
                        "user_id": user_id,
                        "request_id": request_id,
                    },
                )

                if reraise:
                    raise

                return None

        return wrapper

    return decorator


class CircuitBreaker:
    """Circuit breaker pattern for external service calls with metrics"""

    def __init__(
        self, failure_threshold: int = 5, timeout: int = 60, name: str = "circuit"
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open
        self.name = name

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call function with circuit breaker protection"""

        if self.state == "open":
            if self._should_attempt_reset():
                self.state = "half-open"
                circuit_breaker_state.labels(self.name, "half_open").inc()
            else:
                circuit_breaker_state.labels(self.name, "open").inc()
                raise CircuitBreakerError("Circuit breaker is open")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception:
            self._on_failure()
            raise

    def _should_attempt_reset(self) -> bool:
        """Check if we should attempt to reset the circuit"""
        return (
            self.last_failure_time
            and time.time() - self.last_failure_time >= self.timeout
        )

    def _on_success(self):
        """Handle successful call"""
        self.failure_count = 0
        if self.state != "closed":
            circuit_breaker_state.labels(self.name, "closed").inc()
        self.state = "closed"

    def _on_failure(self):
        """Handle failed call"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            if self.state != "open":
                circuit_breaker_state.labels(self.name, "open").inc()
            self.state = "open"


# Retry decorator with exponential backoff
def with_retry(
    max_attempts: int = 3,
    delay: float = 1.0,
    exponential_backoff: bool = True,
    exceptions: tuple = (Exception,),
):
    """Retry decorator with exponential backoff"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts - 1:
                        raise

                    wait_time = delay * (2**attempt) if exponential_backoff else delay
                    time.sleep(wait_time)

                    error_handler.handle_error(
                        e,
                        severity=ErrorSeverity.LOW,
                        context={
                            "attempt": attempt + 1,
                            "max_attempts": max_attempts,
                            "function": func.__name__,
                        },
                    )

        return wrapper

    return decorator
