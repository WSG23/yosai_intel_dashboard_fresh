"""Feature flag audit logging utilities."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from plugins.compliance_plugin.services.audit_logger import ComplianceAuditLogger
from yosai_intel_dashboard.src.core.container import container


def _get_audit_logger() -> ComplianceAuditLogger:
    """Retrieve the global :class:`ComplianceAuditLogger` instance."""
    if container.has("compliance_audit_logger"):
        return container.get("compliance_audit_logger")
    return container.get("audit_logger")


def log_feature_flag_created(
    name: str, new_value: bool, user_id: str, reason: str
) -> str:
    """Log creation of a feature flag."""
    logger = _get_audit_logger()
    timestamp = datetime.now(timezone.utc).isoformat()
    return logger.log_action(
        actor_user_id=user_id,
        action_type="FEATURE_FLAG_CREATE",
        resource_type="feature_flag",
        resource_id=name,
        description=f"Created feature flag '{name}'",
        metadata={
            "old_value": None,
            "new_value": new_value,
            "reason": reason,
            "timestamp": timestamp,
        },
    )


def log_feature_flag_updated(
    name: str, old_value: bool, new_value: bool, user_id: str, reason: str
) -> str:
    """Log update of a feature flag."""
    logger = _get_audit_logger()
    timestamp = datetime.now(timezone.utc).isoformat()
    return logger.log_action(
        actor_user_id=user_id,
        action_type="FEATURE_FLAG_UPDATE",
        resource_type="feature_flag",
        resource_id=name,
        description=f"Updated feature flag '{name}'",
        metadata={
            "old_value": old_value,
            "new_value": new_value,
            "reason": reason,
            "timestamp": timestamp,
        },
    )


def log_feature_flag_deleted(
    name: str, old_value: bool, user_id: str, reason: str
) -> str:
    """Log deletion of a feature flag."""
    logger = _get_audit_logger()
    timestamp = datetime.now(timezone.utc).isoformat()
    return logger.log_action(
        actor_user_id=user_id,
        action_type="FEATURE_FLAG_DELETE",
        resource_type="feature_flag",
        resource_id=name,
        description=f"Deleted feature flag '{name}'",
        metadata={
            "old_value": old_value,
            "new_value": None,
            "reason": reason,
            "timestamp": timestamp,
        },
    )


def get_feature_flag_audit_history(name: str, limit: int = 100) -> List[Dict[str, Any]]:
    """Return audit log entries for a feature flag."""
    logger = _get_audit_logger()
    logs = logger.search_audit_logs(limit=limit)
    return [
        log
        for log in logs
        if log.get("resource_type") == "feature_flag" and log.get("resource_id") == name
    ]
