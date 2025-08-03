from __future__ import annotations

"""User aware rate limiter with RBAC integration."""

import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import (
    dynamic_config,
)
from yosai_intel_dashboard.src.core.rbac import RBACService, _run_sync as _rbac_run_sync

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tier mappings
_BASE_LIMIT = dynamic_config.security.rate_limit_requests
_TIER_LIMITS: Dict[str, Optional[int]] = {
    "free": _BASE_LIMIT,
    "pro": _BASE_LIMIT * 10,
    "enterprise": _BASE_LIMIT * 100,
    "admin": None,  # unlimited
}

_ROLE_TIER: Dict[str, str] = {
    "admin": "admin",
    "enterprise": "enterprise",
    "pro": "pro",
    "free": "free",
}

_PERMISSION_TIER: Dict[str, str] = {
    "tier:enterprise": "enterprise",
    "tier:pro": "pro",
    "tier:free": "free",
}


def get_rate_limit_tier(
    user_id: str, service: Optional[RBACService]
) -> Tuple[str, Optional[int]]:
    """Return the API tier and request limit for *user_id*.

    Roles are queried from ``RBACService``.  If the user has the ``admin`` role
    they are treated as unlimited.  Roles and permissions are mapped to tiers
    (``free``, ``pro`` and ``enterprise``) with corresponding request limits.
    If no role or permission matches, the ``free`` tier is assumed.
    """

    if service is None:
        return "free", _TIER_LIMITS["free"]

    try:
        roles = _rbac_run_sync(service.get_roles(user_id))
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("failed to fetch roles for %s: %s", user_id, exc)
        roles = []

    if "admin" in roles:
        return "admin", _TIER_LIMITS["admin"]

    for role in roles:
        tier = _ROLE_TIER.get(role)
        if tier:
            return tier, _TIER_LIMITS.get(tier)

    try:
        perms = _rbac_run_sync(service.get_permissions(user_id))
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning("failed to fetch permissions for %s: %s", user_id, exc)
        perms = []

    for perm in perms:
        tier = _PERMISSION_TIER.get(perm)
        if tier:
            return tier, _TIER_LIMITS.get(tier)

    return "free", _TIER_LIMITS["free"]


# ---------------------------------------------------------------------------
@dataclass
class RateLimiter:
    """Rate limiting to prevent abuse with RBAC awareness."""

    max_requests: int = _BASE_LIMIT
    window_minutes: int = dynamic_config.security.rate_limit_window_minutes
    rbac_service: Optional[RBACService] = None

    def __post_init__(self) -> None:  # noqa: D401 - dataclass hook
        self.window_seconds = self.window_minutes * 60
        self.requests: Dict[str, List[float]] = {}
        self.blocked_ips: Dict[str, float] = {}
        self.logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------
    def _limit_for(self, user_id: Optional[str]) -> Tuple[str, Optional[int]]:
        if not user_id:
            return "free", self.max_requests
        tier, limit = get_rate_limit_tier(user_id, self.rbac_service)
        if limit is None:
            return tier, None
        return tier, limit

    # ------------------------------------------------------------------
    def is_allowed(
        self, identifier: str, source_ip: Optional[str] = None, user_id: Optional[str] = None
    ) -> Dict[str, any]:
        """Check if request from *identifier* is within its allowed limit."""
        current_time = time.time()

        # Check if IP is blocked
        if source_ip and source_ip in self.blocked_ips:
            if current_time < self.blocked_ips[source_ip]:
                return {
                    "allowed": False,
                    "reason": "IP temporarily blocked",
                    "retry_after": self.blocked_ips[source_ip] - current_time,
                }
            del self.blocked_ips[source_ip]

        tier, limit = self._limit_for(user_id)
        if limit is None:
            return {"allowed": True, "tier": tier, "remaining": float("inf")}

        # Initialize or clean old requests
        history = self.requests.setdefault(identifier, [])
        cutoff = current_time - self.window_seconds
        self.requests[identifier] = [t for t in history if t > cutoff]

        if len(self.requests[identifier]) >= limit:
            if source_ip:
                self.blocked_ips[source_ip] = current_time + (self.window_seconds * 2)
                self.logger.warning("Rate limit exceeded, blocking IP: %s", source_ip)
            return {
                "allowed": False,
                "reason": "Rate limit exceeded",
                "requests_in_window": len(self.requests[identifier]),
                "max_requests": limit,
                "window_seconds": self.window_seconds,
                "tier": tier,
            }

        self.requests[identifier].append(current_time)
        return {
            "allowed": True,
            "requests_in_window": len(self.requests[identifier]),
            "remaining": limit - len(self.requests[identifier]),
            "tier": tier,
        }
