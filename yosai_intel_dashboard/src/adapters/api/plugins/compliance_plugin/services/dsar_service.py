# services/compliance/dsar_service.py
"""Data Subject Access Request (DSAR) Service for GDPR/APPI Compliance"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Protocol
from uuid import uuid4

from core.audit_logger import ComplianceAuditLogger
from core.protocols import DatabaseProtocol
from core.unicode import safe_unicode_encode
from database.secure_exec import execute_command, execute_query
from yosai_intel_dashboard.models.compliance import (
    DSARRequest,
    DSARRequestType,
    DSARStatus,
)

logger = logging.getLogger(__name__)


class DSARServiceProtocol(Protocol):
    """Protocol for DSAR operations"""

    def create_request(
        self, user_id: str, request_type: DSARRequestType, email: str
    ) -> str:
        """Create new DSAR request"""
        ...

    def process_request(self, request_id: str, processed_by: str) -> bool:
        """Process pending DSAR request"""
        ...


class DSARService:
    """Handles Data Subject Access Requests for user rights"""

    def __init__(self, db: DatabaseProtocol, audit_logger: ComplianceAuditLogger):
        self.db = db
        self.audit_logger = audit_logger

        # Jurisdiction-specific response times (days)
        self._response_times = {
            "EU": 30,  # GDPR Article 12
            "JP": 30,  # APPI similar timeframe
            "US": 45,  # CCPA
            "DEFAULT": 30,
        }

    def create_request(
        self,
        user_id: str,
        request_type: DSARRequestType,
        requestor_email: str,
        jurisdiction: str = "EU",
        request_details: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create new DSAR request

        Returns:
            str: Request ID for tracking
        """
        try:
            request_id = (
                f"DSAR-{datetime.now().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}"
            )

            # Calculate due date based on jurisdiction
            response_days = self._response_times.get(
                jurisdiction, self._response_times["DEFAULT"]
            )
            due_date = datetime.now(timezone.utc) + timedelta(days=response_days)

            # Insert request record
            insert_sql = """
                INSERT INTO dsar_requests 
                (id, request_id, user_id, request_type, status, jurisdiction,
                 received_date, due_date, requestor_email, request_details, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            request_uuid = uuid4()
            now = datetime.now(timezone.utc)

            execute_command(
                self.db,
                insert_sql,
                (
                    str(request_uuid),
                    request_id,
                    user_id,
                    request_type.value,
                    DSARStatus.PENDING.value,
                    jurisdiction,
                    now,
                    due_date,
                    requestor_email,
                    json.dumps(request_details) if request_details else None,
                    now,
                    now,
                ),
            )

            # Audit log the request creation
            self.audit_logger.log_action(
                actor_user_id=user_id,
                target_user_id=user_id,
                action_type="CREATE_DSAR_REQUEST",
                resource_type="dsar_request",
                resource_id=request_id,
                description=f"Created {request_type.value} request",
                legal_basis="data_subject_rights",
                data_categories=["user_requests"],
            )

            logger.info(f"DSAR request created: {request_id} for user {user_id}")
            return request_id

        except Exception as e:
            logger.error(f"Failed to create DSAR request: {e}")
            raise

    def process_request(self, request_id: str, processed_by: str) -> bool:
        """Process a pending DSAR request"""
        try:
            # Get request details
            request_data = self._get_request(request_id)
            if not request_data:
                logger.error(f"DSAR request not found: {request_id}")
                return False

            if request_data["status"] != DSARStatus.PENDING.value:
                logger.warning(f"DSAR request {request_id} is not pending")
                return False

            # Update status to in progress
            self._update_request_status(
                request_id, DSARStatus.IN_PROGRESS, processed_by
            )

            # Process based on request type
            request_type = DSARRequestType(request_data["request_type"])
            user_id = request_data["user_id"]

            success = False
            response_data = None

            if request_type == DSARRequestType.ACCESS:
                response_data = self._process_access_request(user_id)
                success = response_data is not None

            elif request_type == DSARRequestType.PORTABILITY:
                response_data = self._process_portability_request(user_id)
                success = response_data is not None

            elif request_type == DSARRequestType.ERASURE:
                success = self._process_erasure_request(user_id)

            elif request_type == DSARRequestType.RECTIFICATION:
                success = self._process_rectification_request(
                    user_id, request_data.get("request_details", {})
                )

            elif request_type == DSARRequestType.RESTRICTION:
                success = self._process_restriction_request(user_id)

            # Update final status
            final_status = DSARStatus.COMPLETED if success else DSARStatus.REJECTED
            self._complete_request(
                request_id, final_status, processed_by, response_data
            )

            # Audit log completion
            self.audit_logger.log_action(
                actor_user_id=processed_by,
                target_user_id=user_id,
                action_type="COMPLETE_DSAR_REQUEST",
                resource_type="dsar_request",
                resource_id=request_id,
                description=f"Completed {request_type.value} request with status {final_status.value}",
                legal_basis="data_subject_rights",
            )

            logger.info(
                f"DSAR request processed: {request_id}, status: {final_status.value}"
            )
            return success

        except Exception as e:
            logger.error(f"Failed to process DSAR request {request_id}: {e}")
            return False

    def _process_access_request(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Process data access request - return all user data"""
        try:
            user_data = {}

            # Get user profile data
            from services.optimized_queries import OptimizedQueryService

            query_service = OptimizedQueryService(self.db)
            users = query_service.batch_get_users([user_id])
            if users:
                user_data["profile"] = users[0]

            # Get access events
            events_query = """
                SELECT ae.*, p.*
                FROM access_events ae
                JOIN people p ON ae.person_id = p.person_id
                WHERE ae.person_id = %s
                ORDER BY ae.timestamp DESC
                LIMIT 1000
            """
            events_df = execute_query(self.db, events_query, (user_id,))
            user_data["access_events"] = (
                events_df.to_dict("records") if not events_df.empty else []
            )

            # Get consent history
            consent_sql = """
                SELECT consent_type, jurisdiction, is_active, granted_timestamp,
                       withdrawn_timestamp, policy_version, legal_basis
                FROM consent_log 
                WHERE user_id = %s
                ORDER BY granted_timestamp DESC
            """
            consent_df = execute_query(self.db, consent_sql, (user_id,))
            user_data["consent_history"] = (
                consent_df.to_dict("records") if not consent_df.empty else []
            )

            # Get anomaly detections
            anomaly_sql = """
                SELECT ad.anomaly_id, ad.anomaly_type, ad.severity, ad.confidence_score,
                       ad.description, ad.detected_at, ad.ai_model_version
                FROM anomaly_detections ad
                JOIN access_events ae ON ad.event_id = ae.event_id
                WHERE ae.person_id = %s
                ORDER BY ad.detected_at DESC
            """
            anomaly_df = execute_query(self.db, anomaly_sql, (user_id,))
            user_data["anomaly_detections"] = (
                anomaly_df.to_dict("records") if not anomaly_df.empty else []
            )

            # Add metadata
            user_data["export_metadata"] = {
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
                "user_id": user_id,
                "data_categories": [
                    "profile",
                    "access_events",
                    "consent_history",
                    "anomaly_detections",
                ],
                "export_format": "json",
            }

            return user_data

        except Exception as e:
            logger.error(f"Failed to process access request for {user_id}: {e}")
            return None

    def _process_portability_request(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Process data portability request - return data in structured format"""
        # Similar to access but focused on portable data
        access_data = self._process_access_request(user_id)
        if not access_data:
            return None

        # Format for portability (remove internal IDs, clean up format)
        portable_data = {
            "user_profile": access_data.get("profile", {}),
            "access_history": access_data.get("access_events", []),
            "consent_preferences": access_data.get("consent_history", []),
            "export_info": {
                "format": "json",
                "schema_version": "1.0",
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "rights_exercised": "data_portability",
            },
        }

        return portable_data

    def _process_erasure_request(self, user_id: str) -> bool:
        """Process right to erasure/be forgotten request"""
        try:
            # 1. Pseudonymize access events (keep for security logs but remove personal identifiers)
            pseudonym_id = f"DELETED_USER_{str(uuid4())[:8].upper()}"

            update_events_sql = """
                UPDATE access_events 
                SET person_id = %s, badge_id = CONCAT('DELETED_', badge_id)
                WHERE person_id = %s
            """
            execute_command(self.db, update_events_sql, (pseudonym_id, user_id))

            # 2. Delete biometric templates and sensitive data
            delete_biometric_sql = """
                DELETE FROM biometric_templates 
                WHERE person_id = %s
            """
            execute_command(self.db, delete_biometric_sql, (user_id,))

            # 3. Anonymize user profile
            update_profile_sql = """
                UPDATE people 
                SET name = 'DELETED USER', 
                    employee_id = %s,
                    department = 'DELETED',
                    data_sensitivity_level = 'anonymized'
                WHERE person_id = %s
            """
            execute_command(self.db, update_profile_sql, (pseudonym_id, user_id))

            # 4. Withdraw all active consents
            update_consent_sql = """
                UPDATE consent_log 
                SET is_active = FALSE, withdrawn_timestamp = %s
                WHERE user_id = %s AND is_active = TRUE
            """
            execute_command(
                self.db, update_consent_sql, (datetime.now(timezone.utc), user_id)
            )

            logger.info(f"Erasure completed for user {user_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to process erasure request for {user_id}: {e}")
            return False

    def _process_rectification_request(
        self, user_id: str, request_details: Dict[str, Any]
    ) -> bool:
        """Process data rectification request"""
        try:
            # Extract fields to update from request details
            updates = request_details.get("updates", {})
            if not updates:
                logger.warning(
                    f"No updates specified in rectification request for {user_id}"
                )
                return False

            # Build dynamic update query (be careful with SQL injection)
            allowed_fields = ["name", "department", "clearance_level"]
            update_clauses = []
            params = []

            for field, value in updates.items():
                if field in allowed_fields:
                    update_clauses.append(f"{field} = %s")
                    params.append(value)

            if not update_clauses:
                logger.warning(f"No valid fields to update for user {user_id}")
                return False

            update_sql = f"""
                UPDATE people 
                SET {', '.join(update_clauses)}, updated_at = %s
                WHERE person_id = %s
            """
            params.extend([datetime.now(timezone.utc), user_id])

            rows_affected = execute_command(self.db, update_sql, tuple(params))

            if rows_affected > 0:
                logger.info(f"Rectification completed for user {user_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to process rectification request for {user_id}: {e}")
            return False

    def _process_restriction_request(self, user_id: str) -> bool:
        """Process restriction of processing request"""
        try:
            # Add restriction flag to user profile
            update_sql = """
                UPDATE people 
                SET consent_status = jsonb_set(
                    COALESCE(consent_status, '{}'), 
                    '{processing_restricted}', 
                    'true'
                )
                WHERE person_id = %s
            """

            rows_affected = execute_command(self.db, update_sql, (user_id,))

            if rows_affected > 0:
                logger.info(f"Processing restriction applied for user {user_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to process restriction request for {user_id}: {e}")
            return False

    def get_pending_requests(self, due_within_days: int = 7) -> List[Dict[str, Any]]:
        """Get DSAR requests that are due soon"""
        try:
            due_date = datetime.now(timezone.utc) + timedelta(days=due_within_days)

            query_sql = """
                SELECT request_id, user_id, request_type, status, jurisdiction,
                       received_date, due_date, requestor_email
                FROM dsar_requests 
                WHERE status IN ('pending', 'in_progress') 
                  AND due_date <= %s
                ORDER BY due_date ASC
            """

            df = execute_query(self.db, query_sql, (due_date,))
            return df.to_dict("records") if not df.empty else []

        except Exception as e:
            logger.error(f"Failed to get pending requests: {e}")
            return []

    def _get_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Get request details by ID"""
        try:
            query_sql = """
                SELECT id, request_id, user_id, request_type, status, jurisdiction,
                       received_date, due_date, requestor_email, request_details
                FROM dsar_requests 
                WHERE request_id = %s
            """

            df = execute_query(self.db, query_sql, (request_id,))
            return df.iloc[0].to_dict() if not df.empty else None

        except Exception as e:
            logger.error(f"Failed to get request {request_id}: {e}")
            return None

    def _update_request_status(
        self, request_id: str, status: DSARStatus, processed_by: str
    ):
        """Update request status"""
        update_sql = """
            UPDATE dsar_requests 
            SET status = %s, processed_by = %s, updated_at = %s
            WHERE request_id = %s
        """

        execute_command(
            self.db,
            update_sql,
            (status.value, processed_by, datetime.now(timezone.utc), request_id),
        )

    def _complete_request(
        self,
        request_id: str,
        status: DSARStatus,
        processed_by: str,
        response_data: Optional[Dict[str, Any]],
    ):
        """Complete request with final status and response data"""
        update_sql = """
            UPDATE dsar_requests 
            SET status = %s, fulfilled_date = %s, processed_by = %s, 
                response_data = %s, updated_at = %s
            WHERE request_id = %s
        """

        # Safely encode response data to handle Unicode issues
        response_json = None
        if response_data:
            try:
                response_json = json.dumps(
                    response_data, ensure_ascii=False, default=str
                )
                response_json = safe_unicode_encode(response_json)
            except Exception as e:
                logger.error(f"Failed to encode response data: {e}")
                response_json = '{"error": "Failed to encode response data"}'

        execute_command(
            self.db,
            update_sql,
            (
                status.value,
                datetime.now(timezone.utc),
                processed_by,
                response_json,
                datetime.now(timezone.utc),
                request_id,
            ),
        )


# Factory function for DI container
def create_dsar_service(
    db: DatabaseProtocol, audit_logger: ComplianceAuditLogger
) -> DSARService:
    """Create DSAR service instance"""
    return DSARService(db, audit_logger)
