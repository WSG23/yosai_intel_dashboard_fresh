# services/compliance/data_retention_service.py
"""Data Retention and Anonymization Service for GDPR/APPI Compliance"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Protocol
from uuid import uuid4

from core.audit_logger import ComplianceAuditLogger
from yosai_intel_dashboard.src.core.interfaces.protocols import DatabaseProtocol
from database.secure_exec import execute_command, execute_query
from yosai_intel_dashboard.models.compliance import DataSensitivityLevel

logger = logging.getLogger(__name__)


class RetentionPolicy:
    """Data retention policy definition"""

    def __init__(
        self,
        data_type: str,
        retention_days: int,
        legal_basis: str,
        jurisdiction: str,
        anonymization_required: bool = True,
        hard_delete_required: bool = False,
    ):
        self.data_type = data_type
        self.retention_days = retention_days
        self.legal_basis = legal_basis
        self.jurisdiction = jurisdiction
        self.anonymization_required = anonymization_required
        self.hard_delete_required = hard_delete_required


class DataRetentionServiceProtocol(Protocol):
    """Protocol for data retention operations"""

    def apply_retention_policy(self, data_type: str, user_id: str) -> bool:
        """Apply retention policy to specific user data"""
        ...

    def schedule_deletion(
        self, user_id: str, data_types: List[str], retention_days: int
    ) -> bool:
        """Schedule data for deletion after retention period"""
        ...


class DataRetentionService:
    """Manages data retention and anonymization according to policies"""

    def __init__(self, db: DatabaseProtocol, audit_logger: ComplianceAuditLogger):
        self.db = db
        self.audit_logger = audit_logger

        # Default retention policies (customize per your requirements)
        self._default_policies = {
            "biometric_templates": RetentionPolicy(
                data_type="biometric_templates",
                retention_days=365,  # 1 year
                legal_basis="consent",
                jurisdiction="EU",
                hard_delete_required=True,  # Biometric data requires hard deletion
            ),
            "access_logs": RetentionPolicy(
                data_type="access_logs",
                retention_days=2555,  # 7 years for security logs
                legal_basis="legitimate_interests",
                jurisdiction="EU",
                anonymization_required=True,
                hard_delete_required=False,
            ),
            "user_profiles": RetentionPolicy(
                data_type="user_profiles",
                retention_days=730,  # 2 years after account closure
                legal_basis="contract",
                jurisdiction="EU",
                anonymization_required=True,
            ),
            "consent_records": RetentionPolicy(
                data_type="consent_records",
                retention_days=2555,  # 7 years for legal compliance
                legal_basis="legal_obligation",
                jurisdiction="EU",
                anonymization_required=False,
                hard_delete_required=False,
            ),
            "analytical_data": RetentionPolicy(
                data_type="analytical_data",
                retention_days=1095,  # 3 years
                legal_basis="legitimate_interests",
                jurisdiction="EU",
                anonymization_required=True,
            ),
        }

    def apply_retention_policy(self, data_type: str, user_id: str) -> bool:
        """Apply retention policy to specific user data type"""
        try:
            policy = self._get_retention_policy(data_type)
            if not policy:
                logger.warning(f"No retention policy found for data type: {data_type}")
                return False

            if policy.hard_delete_required:
                success = self._hard_delete_data(user_id, data_type)
            elif policy.anonymization_required:
                success = self._anonymize_data(user_id, data_type)
            else:
                # Keep data but mark as processed
                success = self._mark_retention_processed(user_id, data_type)

            if success:
                # Audit the retention action
                self.audit_logger.log_data_deletion(
                    actor_user_id="system",
                    target_user_id=user_id,
                    data_types=[data_type],
                    retention_policy=f"{data_type}_{policy.retention_days}d",
                )

                logger.info(
                    f"Applied retention policy for {data_type} on user {user_id}"
                )

            return success

        except Exception as e:
            logger.error(f"Failed to apply retention policy: {e}")
            return False

    def schedule_deletion(
        self, user_id: str, data_types: List[str], retention_days: int
    ) -> bool:
        """Schedule data for deletion after specified retention period"""
        try:
            deletion_date = datetime.now(timezone.utc) + timedelta(days=retention_days)

            # Update user record with deletion schedule
            update_sql = """
                UPDATE people 
                SET data_retention_date = %s,
                    consent_status = jsonb_set(
                        COALESCE(consent_status, '{}'),
                        '{scheduled_deletion}',
                        %s
                    )
                WHERE person_id = %s
            """

            schedule_info = {
                "deletion_date": deletion_date.isoformat(),
                "data_types": data_types,
                "scheduled_at": datetime.now(timezone.utc).isoformat(),
            }

            rows_affected = execute_command(
                self.db, update_sql, (deletion_date, json.dumps(schedule_info), user_id)
            )

            if rows_affected > 0:
                # Audit the scheduling
                self.audit_logger.log_action(
                    actor_user_id="system",
                    target_user_id=user_id,
                    action_type="SCHEDULE_DATA_DELETION",
                    resource_type="retention_schedule",
                    description=f"Scheduled deletion of {', '.join(data_types)} in {retention_days} days",
                    legal_basis="retention_policy",
                    data_categories=data_types,
                    metadata=schedule_info,
                )

                logger.info(f"Scheduled deletion for user {user_id}: {data_types}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to schedule deletion: {e}")
            return False

    def process_scheduled_deletions(self) -> int:
        """Process all data scheduled for deletion (run as scheduled job)"""
        try:
            # Find users with data scheduled for deletion
            query_sql = """
                SELECT person_id, data_retention_date, consent_status
                FROM people
                WHERE data_retention_date IS NOT NULL 
                  AND data_retention_date <= %s
            """

            now = datetime.now(timezone.utc)
            df = execute_query(self.db, query_sql, (now,))

            processed_count = 0

            for row in df.itertuples(index=False):
                user_id = row.person_id
                consent_status = row.consent_status or {}

                if isinstance(consent_status, str):
                    consent_status = json.loads(consent_status)

                data_types = consent_status.get("scheduled_deletion", {}).get(
                    "data_types", ["biometric_templates"]
                )

                processed_count += sum(
                    1
                    for data_type in data_types
                    if self.apply_retention_policy(data_type, user_id)
                )

                self._clear_retention_schedule(user_id)

            logger.info(f"Processed {processed_count} scheduled deletions")
            return processed_count

        except Exception as e:
            logger.error(f"Failed to process scheduled deletions: {e}")
            return 0

    def anonymize_user_completely(self, user_id: str) -> bool:
        """Completely anonymize all user data (for GDPR erasure requests)"""
        try:
            anonymization_id = f"ANON_{str(uuid4())[:8].upper()}"

            # 1. Anonymize user profile
            profile_success = self._anonymize_user_profile(user_id, anonymization_id)

            # 2. Anonymize access events (pseudonymize to maintain security logs)
            events_success = self._anonymize_access_events(user_id, anonymization_id)

            # 3. Hard delete biometric data
            biometric_success = self._hard_delete_biometric_data(user_id)

            # 4. Withdraw all consents
            consent_success = self._withdraw_all_consents(user_id)

            # 5. Anonymize audit logs (keep for legal purposes but remove direct identifiers)
            audit_success = self._anonymize_audit_logs(user_id, anonymization_id)

            success = all(
                [
                    profile_success,
                    events_success,
                    biometric_success,
                    consent_success,
                    audit_success,
                ]
            )

            if success:
                # Final audit log for complete anonymization
                self.audit_logger.log_action(
                    actor_user_id="system",
                    target_user_id=anonymization_id,  # Use anonymized ID
                    action_type="COMPLETE_USER_ANONYMIZATION",
                    resource_type="user_data",
                    description=f"Complete anonymization completed for user (now {anonymization_id})",
                    legal_basis="erasure_request",
                    data_categories=[
                        "profile",
                        "access_events",
                        "biometric_data",
                        "consent_records",
                    ],
                )

                logger.info(
                    f"Complete anonymization successful for user {user_id} -> {anonymization_id}"
                )

            return success

        except Exception as e:
            logger.error(f"Failed to anonymize user {user_id}: {e}")
            return False

    def generate_retention_report(self, days_ahead: int = 30) -> Dict[str, Any]:
        """Generate report of upcoming retention actions"""
        try:
            cutoff_date = datetime.now(timezone.utc) + timedelta(days=days_ahead)

            # Get upcoming deletions
            query_sql = """
                SELECT person_id, data_retention_date, consent_status
                FROM people
                WHERE data_retention_date IS NOT NULL 
                  AND data_retention_date <= %s
                ORDER BY data_retention_date ASC
            """

            df = execute_query(self.db, query_sql, (cutoff_date,))

            upcoming_deletions = []
            for row in df.itertuples(index=False):
                consent_status = row.consent_status or {}
                if isinstance(consent_status, str):
                    consent_status = json.loads(consent_status)

                scheduled_deletion = consent_status.get("scheduled_deletion", {})

                upcoming_deletions.append(
                    {
                        "user_id": row.person_id,
                        "deletion_date": (
                            row.data_retention_date.isoformat()
                            if row.data_retention_date
                            else None
                        ),
                        "data_types": scheduled_deletion.get("data_types", []),
                        "days_remaining": (
                            (row.data_retention_date - datetime.now(timezone.utc)).days
                            if row.data_retention_date
                            else None
                        ),
                    }
                )

            # Get retention policy summary
            policy_summary = {
                policy_name: {
                    "retention_days": policy.retention_days,
                    "legal_basis": policy.legal_basis,
                    "anonymization_required": policy.anonymization_required,
                    "hard_delete_required": policy.hard_delete_required,
                }
                for policy_name, policy in self._default_policies.items()
            }

            return {
                "upcoming_deletions": upcoming_deletions,
                "total_scheduled": len(upcoming_deletions),
                "report_period_days": days_ahead,
                "retention_policies": policy_summary,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to generate retention report: {e}")
            return {"error": str(e)}

    def _get_retention_policy(self, data_type: str) -> Optional[RetentionPolicy]:
        """Get retention policy for data type"""
        return self._default_policies.get(data_type)

    def _hard_delete_data(self, user_id: str, data_type: str) -> bool:
        """Permanently delete data (for sensitive data like biometrics)"""
        try:
            if data_type == "biometric_templates":
                return self._hard_delete_biometric_data(user_id)
            # Add other hard delete cases as needed
            return True
        except Exception as e:
            logger.error(f"Hard delete failed for {data_type}: {e}")
            return False

    def _anonymize_data(self, user_id: str, data_type: str) -> bool:
        """Anonymize data while preserving analytical value"""
        try:
            anonymization_id = f"ANON_{str(uuid4())[:8].upper()}"

            if data_type == "user_profiles":
                return self._anonymize_user_profile(user_id, anonymization_id)
            elif data_type == "access_logs":
                return self._anonymize_access_events(user_id, anonymization_id)
            # Add other anonymization cases as needed

            return True
        except Exception as e:
            logger.error(f"Anonymization failed for {data_type}: {e}")
            return False

    def _anonymize_user_profile(self, user_id: str, anonymization_id: str) -> bool:
        """Anonymize user profile data"""
        try:
            update_sql = """
                UPDATE people 
                SET name = 'ANONYMIZED USER',
                    employee_id = %s,
                    department = 'ANONYMIZED',
                    data_sensitivity_level = 'anonymized'
                WHERE person_id = %s
            """

            rows_affected = execute_command(
                self.db, update_sql, (anonymization_id, user_id)
            )
            return rows_affected > 0
        except Exception as e:
            logger.error(f"Failed to anonymize user profile: {e}")
            return False

    def _anonymize_access_events(self, user_id: str, anonymization_id: str) -> bool:
        """Anonymize access events (pseudonymize for security analysis)"""
        try:
            update_sql = """
                UPDATE access_events 
                SET person_id = %s,
                    badge_id = CONCAT('ANON_', RIGHT(badge_id, 4))
                WHERE person_id = %s
            """

            rows_affected = execute_command(
                self.db, update_sql, (anonymization_id, user_id)
            )
            return True  # Success even if no rows (user might not have events)
        except Exception as e:
            logger.error(f"Failed to anonymize access events: {e}")
            return False

    def _hard_delete_biometric_data(self, user_id: str) -> bool:
        """Permanently delete biometric templates"""
        try:
            # Delete from biometric templates table (if it exists)
            delete_sql = "DELETE FROM biometric_templates WHERE person_id = %s"
            execute_command(self.db, delete_sql, (user_id,))

            # Also remove any biometric flags from access events
            update_events_sql = """
                UPDATE access_events 
                SET contains_biometric_data = FALSE,
                    raw_data = jsonb_set(
                        COALESCE(raw_data, '{}'),
                        '{biometric_data_deleted}',
                        'true'
                    )
                WHERE person_id = %s AND contains_biometric_data = TRUE
            """
            execute_command(self.db, update_events_sql, (user_id,))

            return True
        except Exception as e:
            logger.error(f"Failed to hard delete biometric data: {e}")
            return False

    def _withdraw_all_consents(self, user_id: str) -> bool:
        """Withdraw all active consents for user"""
        try:
            update_sql = """
                UPDATE consent_log 
                SET is_active = FALSE, 
                    withdrawn_timestamp = %s
                WHERE user_id = %s AND is_active = TRUE
            """

            execute_command(self.db, update_sql, (datetime.now(timezone.utc), user_id))
            return True
        except Exception as e:
            logger.error(f"Failed to withdraw consents: {e}")
            return False

    def _anonymize_audit_logs(self, user_id: str, anonymization_id: str) -> bool:
        """Anonymize audit logs while preserving legal records"""
        try:
            # Replace user ID in audit logs with anonymized version
            update_sql = """
                UPDATE compliance_audit_log 
                SET target_user_id = %s
                WHERE target_user_id = %s
            """

            execute_command(self.db, update_sql, (anonymization_id, user_id))
            return True
        except Exception as e:
            logger.error(f"Failed to anonymize audit logs: {e}")
            return False

    def _mark_retention_processed(self, user_id: str, data_type: str) -> bool:
        """Mark data as processed for retention without deletion"""
        try:
            update_sql = """
                UPDATE people 
                SET consent_status = jsonb_set(
                    COALESCE(consent_status, '{}'),
                    '{retention_processed}',
                    jsonb_build_object(%s, %s)
                )
                WHERE person_id = %s
            """

            processed_timestamp = datetime.now(timezone.utc).isoformat()
            execute_command(
                self.db, update_sql, (data_type, processed_timestamp, user_id)
            )
            return True
        except Exception as e:
            logger.error(f"Failed to mark retention processed: {e}")
            return False

    def _clear_retention_schedule(self, user_id: str) -> bool:
        """Clear retention schedule after processing"""
        try:
            update_sql = """
                UPDATE people 
                SET data_retention_date = NULL,
                    consent_status = consent_status - 'scheduled_deletion'
                WHERE person_id = %s
            """

            execute_command(self.db, update_sql, (user_id,))
            return True
        except Exception as e:
            logger.error(f"Failed to clear retention schedule: {e}")
            return False


# Factory function for DI container
def create_data_retention_service(
    db: DatabaseProtocol, audit_logger: ComplianceAuditLogger
) -> DataRetentionService:
    """Create data retention service instance"""
    return DataRetentionService(db, audit_logger)
