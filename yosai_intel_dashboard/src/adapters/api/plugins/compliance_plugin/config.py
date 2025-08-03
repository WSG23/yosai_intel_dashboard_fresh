#!/usr/bin/env python3
"""Compliance plugin configuration"""

from __future__ import annotations

from dataclasses import dataclass, fields
from typing import Any, Dict


@dataclass(frozen=True)
class ComplianceConfig:
    """Configuration for compliance plugin"""

    # Core settings
    enabled: bool = True
    jurisdiction: str = "EU"  # Primary jurisdiction

    # Consent management
    consent_enabled: bool = True
    default_consent_jurisdiction: str = "EU"
    require_explicit_consent: bool = True
    consent_withdrawal_immediate: bool = True

    # Data retention
    retention_enabled: bool = True
    automated_cleanup: bool = True
    cleanup_schedule: str = "02:00"  # Daily at 2 AM
    grace_period_days: int = 30

    # Audit logging
    audit_enabled: bool = True
    audit_retention_days: int = 2555  # 7 years
    audit_encryption_enabled: bool = True

    # DSAR processing
    dsar_enabled: bool = True
    dsar_response_time_hours: int = 72
    dsar_auto_processing: bool = False

    # Breach notification
    breach_notification_enabled: bool = True
    supervisor_notification_hours: int = 72
    individual_notification_enabled: bool = True

    # Cross-border transfers
    transfer_assessment_enabled: bool = True
    adequacy_monitoring: bool = True

    # Dashboard and monitoring
    dashboard_enabled: bool = True
    alerts_enabled: bool = True
    email_notifications: bool = False
    compliance_officer_email: str = ""

    # CSV processing
    csv_compliance_enabled: bool = True
    csv_auto_classification: bool = True
    csv_consent_checking: bool = True

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> "ComplianceConfig":
        """Create a configuration object from a dictionary."""
        valid_fields = {f.name for f in fields(cls)}
        filtered = filter(lambda item: item[0] in valid_fields, config_dict.items())
        return cls(**dict(filtered))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            name: value
            for name, value in map(
                lambda f: (f.name, getattr(self, f.name)), fields(self)
            )
        }
