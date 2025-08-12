# core/security.py
"""
Comprehensive security system for Yōsai Intel Dashboard
Implements Apple's security-by-design principles
"""
from __future__ import annotations

import asyncio
import contextlib
import hashlib
import logging
import os
import secrets
import time
import uuid
# ``ProcessPoolExecutor`` may not be available in some minimal environments.
try:  # pragma: no cover - best effort
    from concurrent.futures import ProcessPoolExecutor
except Exception:  # pragma: no cover
    ProcessPoolExecutor = None  # type: ignore
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum

from typing import Any, Callable, Dict, List, Optional

from argon2 import PasswordHasher
from argon2 import exceptions as argon2_exceptions
import redis.asyncio as redis

_executor = ProcessPoolExecutor() if callable(ProcessPoolExecutor) else None
try:  # pragma: no cover - optional dependency
    _ph = PasswordHasher()
except Exception:  # pragma: no cover
    _ph = None


def _pbkdf2_sha256(password: bytes, salt: bytes, iterations: int) -> bytes:
    """Compute PBKDF2-HMAC-SHA256 hash."""
    return hashlib.pbkdf2_hmac("sha256", password, salt, iterations)


def _sha256_bytes(data: bytes) -> str:
    """Compute SHA256 digest of ``data``."""
    return hashlib.sha256(data).hexdigest()


# Import the high-level ``SecurityValidator`` used across the application.
# This module keeps no internal validation logic and instead delegates to
# :class:`~validation.security_validator.SecurityValidator` for sanitization tasks.
from validation.security_validator import SecurityValidator
from yosai_intel_dashboard.src.core.base_model import BaseModel
from yosai_intel_dashboard.src.core.domain.entities.access_events import (
    AccessEventModel,
)
from yosai_intel_dashboard.src.core.secret_manager import SecretsManager
from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import (
    dynamic_config,
)
from yosai_intel_dashboard.src.infrastructure.monitoring.anomaly_detector import (
    AnomalyDetector,
)


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
class SecurityConfig:
    """Configuration helper for secret retrieval and rotation."""

    secrets_manager: SecretsManager = SecretsManager()

    def __post_init__(self) -> None:  # pragma: no cover - lazy import
        try:
            from yosai_intel_dashboard.src.services.common.secrets import (
                get_secret as _vault_get,
                invalidate_secret as _vault_invalidate,
            )
        except Exception:  # pragma: no cover - optional dependency
            try:  # Fallback for tests using lightweight stubs
                from services.common.secrets import (  # type: ignore
                    get_secret as _vault_get,
                    invalidate_secret as _vault_invalidate,
                )
            except Exception:  # pragma: no cover - vault not available
                _vault_get = _vault_invalidate = None  # type: ignore
        self._vault_get = _vault_get
        self._vault_invalidate = _vault_invalidate

    def get_secret(
        self,
        env_key: str,
        *,
        vault_key: str | None = None,
        default: str | None = None,
        rotate: bool = False,
    ) -> str:
        """Return secret value from environment or Vault.

        When ``vault_key`` is provided and Vault access is configured it is
        preferred. Passing ``rotate=True`` will invalidate any cached Vault
        value before retrieving it.
        """

        if rotate and vault_key and self._vault_invalidate:
            self._vault_invalidate(vault_key)
        if vault_key and self._vault_get:
            try:
                return self._vault_get(vault_key)
            except Exception:  # pragma: no cover - fall back to env
                pass
        value = self.secrets_manager.get(env_key, default)
        if value is None:
            raise RuntimeError(f"missing secret {env_key}")
        return value


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
    """Redis backed sliding window limiter with IP blocking and memory fallback."""

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        tier_config: Optional[Dict[str, Dict[str, int]]] = None,
        window: int = dynamic_config.security.rate_limit_window_minutes * 60,
        limit: int = dynamic_config.security.rate_limit_requests,
        burst: int = 0,
        key_prefix: str = "rl:",
        block_prefix: str = "rl:block:",
    ) -> None:
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.block_prefix = block_prefix
        self.default_config = {"window": window, "limit": limit, "burst": burst}
        self.tier_config = tier_config or {}
        self._memory: Dict[str, List[float]] = {}
        self._blocked_ips: Dict[str, float] = {}
        self.logger = logging.getLogger(__name__)
        self._cleanup_task: asyncio.Task | None = None
        # Compatibility attributes used by existing code
        self.max_requests = limit

    def _get_config(self, tier: str) -> Dict[str, int]:
        return self.tier_config.get(tier, self.default_config)

    def _build_key(self, identifier: str, tier: str) -> str:
        return f"{self.key_prefix}{tier}:{identifier}"

    async def is_allowed(
        self, identifier: Optional[str], ip: str | None = None, tier: str = "default"
    ) -> Dict[str, float]:
        """Check rate limit for ``identifier`` or ``ip`` within given ``tier``."""

        ident = identifier or ip or "anonymous"
        cfg = self._get_config(tier)
        window = cfg["window"]
        limit = cfg["limit"]
        burst = cfg.get("burst", 0)
        now = time.time()

        if ip:
            block_key = f"{self.block_prefix}{ip}"
            if self.redis is not None:
                ttl = await self.redis.ttl(block_key)
                if ttl > 0:
                    return {
                        "allowed": False,
                        "reason": "IP temporarily blocked",
                        "retry_after": ttl,
                        "limit": limit,
                        "remaining": 0,
                        "reset": now + ttl,
                    }
            else:
                expiry = self._blocked_ips.get(ip)
                if expiry and expiry > now:
                    retry = int(expiry - now)
                    return {
                        "allowed": False,
                        "reason": "IP temporarily blocked",
                        "retry_after": retry,
                        "limit": limit,
                        "remaining": 0,
                        "reset": now + retry,
                    }

        key = self._build_key(ident, tier)
        if self.redis is not None:
            member = f"{now}-{uuid.uuid4().hex}"
            try:
                pipe = self.redis.pipeline()
                pipe.zadd(key, {member: now})
                pipe.zremrangebyscore(key, 0, now - window)
                pipe.zcard(key)
                pipe.zrange(key, 0, 0, withscores=True)
                pipe.expire(key, window)
                _, _, count, oldest, _ = await pipe.execute()
                count = int(count)
                allowed = count <= limit + burst
                if not allowed:
                    await self.redis.zrem(key, member)
                    if ip:
                        await self.redis.set(block_key, 1, ex=window * 2)
                        self.logger.warning(
                            "Rate limit exceeded, blocking IP: %s", ip
                        )
                remaining = max(0, limit + burst - (count if allowed else count - 1))
                if oldest:
                    oldest_score = float(oldest[0][1])
                    reset = max(0, window - (now - oldest_score))
                else:
                    reset = window
                result = {
                    "allowed": allowed,
                    "remaining": remaining,
                    "limit": limit,
                    "reset": reset,
                }
                if not allowed:
                    result["retry_after"] = reset
                    result["reason"] = "Rate limit exceeded"
                return result
            except Exception as exc:  # pragma: no cover - best effort
                self.logger.warning("Redis rate limit check failed for %s: %s", key, exc)

        # Fallback to in-memory implementation
        timestamps = self._memory.setdefault(key, [])
        cutoff = now - window
        timestamps[:] = [ts for ts in timestamps if ts > cutoff]
        allowed = len(timestamps) < limit + burst
        if allowed:
            timestamps.append(now)
        else:
            if ip:
                self._blocked_ips[ip] = now + window * 2
                self.logger.warning("Rate limit exceeded, blocking IP: %s", ip)
        remaining = max(0, limit + burst - len(timestamps))
        if timestamps:
            reset = max(0, window - (now - timestamps[0]))
        else:
            reset = window
        result = {"allowed": allowed, "remaining": remaining, "limit": limit, "reset": reset}
        if not allowed:
            result["retry_after"] = reset
            result["reason"] = "Rate limit exceeded"
        return result

    async def _cleanup_blocked_ips(self) -> None:
        while True:
            if self.redis is not None:
                async for key in self.redis.scan_iter(match=f"{self.block_prefix}*"):
                    ttl = await self.redis.ttl(key)
                    if ttl <= 0:
                        await self.redis.delete(key)
            else:
                now = time.time()
                self._blocked_ips = {
                    ip: exp for ip, exp in self._blocked_ips.items() if exp > now
                }
            await asyncio.sleep(self.default_config["window"])

    def start_cleanup(self) -> None:
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_blocked_ips())

    async def stop_cleanup(self) -> None:
        if self._cleanup_task:
            self._cleanup_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._cleanup_task
            self._cleanup_task = None


async def create_rate_limiter(
    tier_config: Optional[Dict[str, Dict[str, int]]] = None,
    window: int = dynamic_config.security.rate_limit_window_minutes * 60,
    limit: int = dynamic_config.security.rate_limit_requests,
    burst: int = 0,
) -> RateLimiter:
    """Factory to create :class:`RateLimiter` with Redis connection."""

    redis_client: Optional[redis.Redis] = None
    try:
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
        )
        await redis_client.ping()
    except Exception:  # pragma: no cover - best effort
        redis_client = None
    return RateLimiter(redis_client, tier_config, window, limit, burst)


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
        timestamps = [e.timestamp for e in self.events]
        idx = bisect_left(timestamps, cutoff)
        recent_events = self.events[idx:]

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
    def hash_password(password: str) -> Dict[str, str]:
        """Hash password using Argon2."""
        hashed = _ph.hash(password)
        return {"hash": hashed, "algorithm": "argon2"}

    @staticmethod
    def verify_password(
        password: str,
        stored_hash: str,
        stored_salt: str | None = None,
        algorithm: str | None = None,
    ) -> tuple[bool, str]:
        """Verify password and migrate legacy hashes.

        Returns tuple of verification result and current hash.
        """
        algo = algorithm or "argon2"
        if algo == "argon2":
            try:
                _ph.verify(stored_hash, password)
                return True, stored_hash
            except argon2_exceptions.VerifyMismatchError:
                return False, stored_hash
        # Legacy PBKDF2 verification
        if stored_salt is None:
            return False, stored_hash
        salt = bytes.fromhex(stored_salt)
        future = _executor.submit(
            _pbkdf2_sha256,
            password.encode(),
            salt,
            dynamic_config.security.pbkdf2_iterations,
        )
        hash_bytes = future.result()
        if hash_bytes.hex() == stored_hash:
            # migrate to argon2
            new_hash = _ph.hash(password)
            return True, new_hash
        return False, stored_hash

    @staticmethod
    def hash_sensitive_data(data: str) -> str:
        """Hash sensitive data for storage"""
        future = _executor.submit(_sha256_bytes, data.encode())
        return future.result()


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


def validate_user_input(value: str, field: str) -> str:
    """Validate and sanitize user input."""
    result = security_validator.validate_input(value, field)
    return result.get("sanitized", value)


rate_limiter = RateLimiter()
security_auditor = SecurityAuditor()
security_config = SecurityConfig()


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


def rate_limit_decorator(limit: int = 100, window_minutes: int = 1):
    """Decorator to apply rate limiting with response headers."""
    limiter = RateLimiter(limit=limit, window=window_minutes * 60)

    def decorator(func):
        from functools import wraps

        from flask import jsonify, make_response, request

        @wraps(func)
        async def wrapper(*args, **kwargs):
            auth = request.headers.get("Authorization", "")
            identifier = (
                auth.split(" ", 1)[1]
                if auth.startswith("Bearer ")
                else request.remote_addr
            )
            result = await limiter.is_allowed(identifier or "anonymous", request.remote_addr)
            headers = {
                "X-RateLimit-Limit": str(result.get("limit", limit)),
                "X-RateLimit-Remaining": str(result.get("remaining", 0)),
                "X-RateLimit-Reset": str(int(result.get("reset", 0))),
            }

            if not result["allowed"]:
                security_auditor.log_security_event(
                    "rate_limit_exceeded",
                    SecurityLevel.MEDIUM,
                    {"function": func.__name__, "reason": result.get("reason", "rate limit exceeded")},
                    blocked=True,
                )
                retry = result.get("retry_after")
                if retry is not None:
                    headers["Retry-After"] = str(int(retry))
                response = jsonify({"detail": "rate limit exceeded"})
                response.status_code = 429
                for key, value in headers.items():
                    response.headers[key] = value
                return response

            if asyncio.iscoroutinefunction(func):
                resp = await func(*args, **kwargs)
            else:
                resp = func(*args, **kwargs)
            response = make_response(resp)
            for key, value in headers.items():
                response.headers[key] = value
            return response

        return wrapper

    return decorator


def initialize_validation_callbacks() -> None:
    """Set up request validation callbacks on import."""
    try:
        from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import (  # noqa: E501
            TrulyUnifiedCallbacks,
        )
        from yosai_intel_dashboard.src.infrastructure.security.validation_middleware import (
            ValidationMiddleware,
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
