"""Feature flag audit helpers."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from yosai_intel_dashboard.src.core.audit_logger import ComplianceAuditLogger

logger = logging.getLogger(__name__)

# This module expects an audit logger instance to be provided by the
# application. Tests inject a dummy logger by assigning to this variable.
audit_logger: Optional[ComplianceAuditLogger] = None


def log_feature_flag_created(
    name: str,
    new_value: Any,
    *,
    actor_user_id: str,
    reason: Optional[str] = None,
    timestamp: Optional[datetime] = None,
) -> None:
    """Record creation of a feature flag."""
    if audit_logger is None:
        return
    metadata = {"new_value": new_value, "reason": reason, "timestamp": timestamp}
    try:
        if hasattr(audit_logger, "log_feature_flag_created"):
            audit_logger.log_feature_flag_created(
                name=name,
                new_value=new_value,
                actor_user_id=actor_user_id,
                reason=reason,
                timestamp=timestamp,
            )
        else:
            audit_logger.log_action(
                actor_user_id=actor_user_id,
                action_type="FEATURE_FLAG_CREATED",
                resource_type="feature_flag",
                resource_id=name,
                description=f"Feature flag {name} created",
                metadata=metadata,
            )
    except Exception:  # pragma: no cover - defensive
        logger.exception("Failed to audit feature flag creation")


def log_feature_flag_updated(
    name: str,
    *,
    old_value: Any,
    new_value: Any,
    actor_user_id: str,
    reason: Optional[str] = None,
    timestamp: Optional[datetime] = None,
) -> None:
    """Record an update to a feature flag."""
    if audit_logger is None:
        return

    metadata = {
        "old_value": old_value,
        "new_value": new_value,
        "reason": reason,
        "timestamp": timestamp,
    }
    try:
        if hasattr(audit_logger, "log_feature_flag_updated"):
            audit_logger.log_feature_flag_updated(
                name=name,
                old_value=old_value,
                new_value=new_value,
                actor_user_id=actor_user_id,
                reason=reason,
                timestamp=timestamp,
            )
        else:
            audit_logger.log_action(
                actor_user_id=actor_user_id,
                action_type="FEATURE_FLAG_UPDATED",
                resource_type="feature_flag",
                resource_id=name,
                description=f"Feature flag {name} updated",
                metadata=metadata,
            )
    except Exception:  # pragma: no cover - defensive
        logger.exception("Failed to audit feature flag update")


def log_feature_flag_deleted(
    name: str,
    *,
    old_value: Any,
    actor_user_id: str,
    reason: Optional[str] = None,
    timestamp: Optional[datetime] = None,
) -> None:
    """Record deletion of a feature flag."""
    if audit_logger is None:
        return
    metadata = {"old_value": old_value, "reason": reason, "timestamp": timestamp}
    try:
        if hasattr(audit_logger, "log_feature_flag_deleted"):
            audit_logger.log_feature_flag_deleted(
                name=name,
                old_value=old_value,
                actor_user_id=actor_user_id,
                reason=reason,
                timestamp=timestamp,
            )
        else:
            audit_logger.log_action(
                actor_user_id=actor_user_id,
                action_type="FEATURE_FLAG_DELETED",
                resource_type="feature_flag",
                resource_id=name,
                description=f"Feature flag {name} deleted",
                metadata=metadata,
            )
    except Exception:  # pragma: no cover - defensive
        logger.exception("Failed to audit feature flag deletion")


def get_feature_flag_audit_history(name: str, limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieve recent audit log entries for a feature flag."""
    if audit_logger is None:
        return []

    try:
        logs = audit_logger.search_audit_logs(
            resource_type="feature_flag",
            resource_id=name,
            limit=limit,
        )
    except Exception:  # pragma: no cover - defensive
        logger.exception("Failed to fetch feature flag audit history")
        return []
    return logs[:limit] if logs else []
