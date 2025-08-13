# services/compliance/consent_service.py
"""Consent Management Service for GDPR/APPI Compliance"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Protocol
from uuid import uuid4

from flask import request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from yosai_intel_dashboard.src.infrastructure.security.query_builder import SecureQueryBuilder
from yosai_intel_dashboard.models.compliance import (
    ConsentLog,
    ConsentType,
    DataSensitivityLevel,
)
from yosai_intel_dashboard.src.core.audit_logger import ComplianceAuditLogger
from yosai_intel_dashboard.src.core.interfaces.protocols import DatabaseProtocol
from yosai_intel_dashboard.src.database.secure_exec import (
    execute_command,
    execute_secure_query,
)

logger = logging.getLogger(__name__)


class ConsentServiceProtocol(Protocol):
    """Protocol for consent management operations"""

    def grant_consent(
        self, user_id: str, consent_type: ConsentType, jurisdiction: str
    ) -> bool:
        """Grant consent for specific processing"""
        ...

    def withdraw_consent(
        self, user_id: str, consent_type: ConsentType, jurisdiction: str
    ) -> bool:
        """Withdraw previously granted consent"""
        ...

    def check_consent(
        self, user_id: str, consent_type: ConsentType, jurisdiction: str
    ) -> bool:
        """Check if valid consent exists"""
        ...


class ConsentService:
    """Manages user consent for data processing activities"""

    def __init__(self, db: DatabaseProtocol, audit_logger: ComplianceAuditLogger):
        self.db = db
        self.audit_logger = audit_logger
        self._policy_version = "1.0"  # Update when privacy policy changes

    def grant_consent(
        self,
        user_id: str,
        consent_type: ConsentType,
        jurisdiction: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """
        Grant consent for specific data processing

        Returns:
            bool: True if consent was successfully granted
        """
        try:
            # Check if active consent already exists
            existing = self._get_active_consent(user_id, consent_type, jurisdiction)
            if existing:
                logger.info(
                    f"Consent already exists for {user_id}, {consent_type.value}, {jurisdiction}"
                )
                return True

            # Create new consent record
            consent = ConsentLog(
                user_id=user_id,
                consent_type=consent_type,
                jurisdiction=jurisdiction,
                is_active=True,
                policy_version=self._policy_version,
                ip_address=ip_address or self._get_client_ip(),
                user_agent=user_agent or self._get_user_agent(),
                legal_basis="consent",
            )

            # Insert into database
            insert_sql = """
                INSERT INTO consent_log 
                (id, user_id, consent_type, jurisdiction, is_active, granted_timestamp, 
                 policy_version, ip_address, user_agent, legal_basis, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            execute_command(
                self.db,
                insert_sql,
                (
                    str(consent.id),
                    consent.user_id,
                    consent.consent_type.value,
                    consent.jurisdiction,
                    consent.is_active,
                    consent.granted_timestamp,
                    consent.policy_version,
                    consent.ip_address,
                    consent.user_agent,
                    consent.legal_basis,
                    consent.created_at,
                ),
            )

            # Audit log the consent grant
            self.audit_logger.log_action(
                actor_user_id=user_id,
                target_user_id=user_id,
                action_type="GRANT_CONSENT",
                resource_type="consent",
                resource_id=str(consent.id),
                description=f"Granted consent for {consent_type.value} in {jurisdiction}",
                legal_basis="consent",
                data_categories=["consent_preferences"],
            )

            logger.info(
                f"Consent granted: {user_id}, {consent_type.value}, {jurisdiction}"
            )
            return True

        except IntegrityError as e:
            logger.error(
                f"Consent already exists or integrity constraint violated: {e}"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to grant consent: {e}")
            return False

    def withdraw_consent(
        self, user_id: str, consent_type: ConsentType, jurisdiction: str
    ) -> bool:
        """
        Withdraw previously granted consent

        Returns:
            bool: True if consent was successfully withdrawn
        """
        try:
            # Find active consent
            consent = self._get_active_consent(user_id, consent_type, jurisdiction)
            if not consent:
                logger.warning(
                    f"No active consent found to withdraw: {user_id}, {consent_type.value}"
                )
                return False

            # Mark as withdrawn
            update_sql = """
                UPDATE consent_log 
                SET is_active = FALSE, withdrawn_timestamp = %s
                WHERE id = %s
            """

            withdrawn_at = datetime.now(timezone.utc)
            rows_affected = execute_command(
                self.db, update_sql, (withdrawn_at, consent["id"])
            )

            if rows_affected > 0:
                # Audit log the withdrawal
                self.audit_logger.log_action(
                    actor_user_id=user_id,
                    target_user_id=user_id,
                    action_type="WITHDRAW_CONSENT",
                    resource_type="consent",
                    resource_id=consent["id"],
                    description=f"Withdrew consent for {consent_type.value} in {jurisdiction}",
                    legal_basis="consent",
                    data_categories=["consent_preferences"],
                )

                # Trigger data processing halt for this consent type
                self._halt_processing_for_consent_type(user_id, consent_type)

                logger.info(
                    f"Consent withdrawn: {user_id}, {consent_type.value}, {jurisdiction}"
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to withdraw consent: {e}")
            return False

    def check_consent(
        self, user_id: str, consent_type: ConsentType, jurisdiction: str
    ) -> bool:
        """
        Check if valid consent exists for processing

        Returns:
            bool: True if valid consent exists
        """
        try:
            consent = self._get_active_consent(user_id, consent_type, jurisdiction)
            return consent is not None
        except Exception as e:
            logger.error(f"Failed to check consent: {e}")
            return False

    def get_user_consents(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all consents for a user (for DSAR requests)"""
        try:
            query_sql = """
                SELECT id, consent_type, jurisdiction, is_active, granted_timestamp,
                       withdrawn_timestamp, policy_version, legal_basis
                FROM consent_log 
                WHERE user_id = %s
                ORDER BY granted_timestamp DESC
            """

            df = execute_secure_query(self.db, query_sql, (user_id,))
            return df.to_dict("records") if not df.empty else []

        except Exception as e:
            logger.error(f"Failed to get user consents: {e}")
            return []

    def bulk_consent_check(
        self, user_ids: List[str], consent_type: ConsentType, jurisdiction: str
    ) -> Dict[str, bool]:
        """Check consent for multiple users efficiently"""
        try:
            if not user_ids:
                return {}

            builder = SecureQueryBuilder(
                allowed_tables={"consent_log"},
                allowed_columns={
                    "user_id",
                    "consent_type",
                    "jurisdiction",
                    "is_active",
                },
            )
            table = builder.table("consent_log")
            user_col = builder.column("user_id")
            consent_col = builder.column("consent_type")
            juris_col = builder.column("jurisdiction")
            active_col = builder.column("is_active")
            placeholders = ",".join(["%s"] * len(user_ids))
            raw_sql = (
                "SELECT DISTINCT "
                + user_col
                + " FROM "
                + table
                + " WHERE "
                + user_col
                + " IN ("
                + placeholders
                + ") AND "
                + consent_col
                + " = %s AND "
                + juris_col
                + " = %s AND "
                + active_col
                + " = TRUE"
            )
            query_sql, _ = builder.build(raw_sql)
            params = tuple(user_ids) + (consent_type.value, jurisdiction)
            df = execute_secure_query(self.db, query_sql, params)

            consented_users = set(df["user_id"].tolist()) if not df.empty else set()

            return {user_id: user_id in consented_users for user_id in user_ids}

        except Exception as e:
            logger.error(f"Failed bulk consent check: {e}")
            return {user_id: False for user_id in user_ids}

    def _get_active_consent(
        self, user_id: str, consent_type: ConsentType, jurisdiction: str
    ) -> Optional[Dict[str, Any]]:
        """Get active consent record"""
        try:
            query_sql = """
                SELECT id, user_id, consent_type, jurisdiction, granted_timestamp, policy_version
                FROM consent_log 
                WHERE user_id = %s 
                  AND consent_type = %s 
                  AND jurisdiction = %s 
                  AND is_active = TRUE
                LIMIT 1
            """

            df = execute_secure_query(
                self.db, query_sql, (user_id, consent_type.value, jurisdiction)
            )
            return df.iloc[0].to_dict() if not df.empty else None

        except Exception as e:
            logger.error(f"Failed to get active consent: {e}")
            return None

    def _halt_processing_for_consent_type(
        self, user_id: str, consent_type: ConsentType
    ):
        """Stop processing activities that depend on withdrawn consent"""
        # Implementation depends on your processing architecture
        # This could trigger:
        # - Stopping real-time analytics for the user
        # - Flagging biometric templates for deletion
        # - Removing user from certain processing queues
        logger.info(f"Halting {consent_type.value} processing for user {user_id}")

        # Example: Mark biometric data for deletion if facial recognition consent withdrawn
        if consent_type == ConsentType.FACIAL_RECOGNITION:
            self._schedule_biometric_deletion(user_id)

    def _schedule_biometric_deletion(self, user_id: str):
        """Schedule biometric data deletion (30-day grace period)"""
        try:
            # Update people table to mark for deletion
            update_sql = """
                UPDATE people 
                SET data_retention_date = %s
                WHERE person_id = %s
            """

            deletion_date = datetime.now(timezone.utc) + timedelta(days=30)
            execute_command(self.db, update_sql, (deletion_date, user_id))

            logger.info(
                f"Scheduled biometric deletion for {user_id} on {deletion_date}"
            )

        except Exception as e:
            logger.error(f"Failed to schedule biometric deletion: {e}")

    def _get_client_ip(self) -> Optional[str]:
        """Get client IP from Flask request"""
        try:
            return request.headers.get("X-Forwarded-For", request.remote_addr)
        except Exception:
            return None

    def _get_user_agent(self) -> Optional[str]:
        """Get user agent from Flask request"""
        try:
            return request.headers.get("User-Agent")
        except Exception:
            return None


# Factory function for DI container
def create_consent_service(
    db: DatabaseProtocol, audit_logger: ComplianceAuditLogger
) -> ConsentService:
    """Create consent service instance"""
    return ConsentService(db, audit_logger)
