# core/audit_logger.py
"""Compliance Audit Logger for GDPR/APPI Requirements"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from flask import g, request
from flask_login import current_user

from core.protocols import DatabaseProtocol
from core.unicode import safe_unicode_encode
from database.secure_exec import execute_command

logger = logging.getLogger(__name__)


class ComplianceAuditLogger:
    """
    Immutable audit logger for all personal data processing activities
    Required for GDPR Article 5(2) accountability and APPI transparency
    """

    def __init__(self, db: DatabaseProtocol):
        self.db = db

    def log_action(
        self,
        actor_user_id: str,
        action_type: str,
        resource_type: str,
        description: str,
        target_user_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        legal_basis: Optional[str] = None,
        data_categories: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> str:
        """
        Log a compliance-relevant action immutably

        Args:
            actor_user_id: User performing the action
            action_type: Type of action (VIEW_PROFILE, DELETE_DATA, etc.)
            resource_type: Type of resource (user_profile, biometric_data, etc.)
            description: Human-readable description of the action
            target_user_id: User whose data is being processed (if different from actor)
            resource_id: Specific resource identifier
            legal_basis: GDPR Article 6 legal basis (consent, legitimate_interests, etc.)
            data_categories: Types of personal data involved
            metadata: Additional structured context
            source_ip: Client IP address
            user_agent: Client user agent
            request_id: Request tracing ID

        Returns:
            str: Audit log entry ID
        """
        try:
            log_id = uuid4()
            now = datetime.now(timezone.utc)

            # Auto-detect Flask request context if available
            if source_ip is None:
                source_ip = self._get_client_ip()
            if user_agent is None:
                user_agent = self._get_user_agent()
            if request_id is None:
                request_id = self._get_request_id()

            # Safely encode description and metadata to handle Unicode issues
            safe_description = safe_unicode_encode(description)
            safe_metadata = None
            if metadata:
                try:
                    import json

                    metadata_json = json.dumps(
                        metadata, ensure_ascii=False, default=str
                    )
                    safe_metadata = safe_unicode_encode(metadata_json)
                except Exception as e:
                    logger.warning(f"Failed to encode audit metadata: {e}")
                    safe_metadata = '{"encoding_error": "Failed to encode metadata"}'

            safe_data_categories = None
            if data_categories:
                try:
                    import json

                    safe_data_categories = json.dumps(
                        data_categories, ensure_ascii=False
                    )
                except Exception as e:
                    logger.warning(f"Failed to encode data categories: {e}")
                    safe_data_categories = '["encoding_error"]'

            # Insert audit log entry
            insert_sql = """
                INSERT INTO compliance_audit_log 
                (id, timestamp, actor_user_id, target_user_id, action_type, resource_type,
                 resource_id, source_ip, user_agent, request_id, description, legal_basis,
                 data_categories, metadata)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            execute_command(
                self.db,
                insert_sql,
                (
                    str(log_id),
                    now,
                    actor_user_id,
                    target_user_id,
                    action_type,
                    resource_type,
                    resource_id,
                    source_ip,
                    user_agent,
                    request_id,
                    safe_description,
                    legal_basis,
                    safe_data_categories,
                    safe_metadata,
                ),
            )

            # Also log to standard logging for real-time monitoring
            logger.info(
                f"AUDIT: {action_type} by {actor_user_id} on {resource_type}"
                f"{f' for {target_user_id}' if target_user_id else ''} - {description}"
            )

            return str(log_id)

        except Exception as e:
            # Audit logging should never fail silently
            logger.error(f"CRITICAL: Failed to write audit log: {e}")
            # Still return an ID to prevent breaking the calling code
            return str(uuid4())

    def log_data_access(
        self,
        actor_user_id: str,
        target_user_id: str,
        data_accessed: List[str],
        purpose: str,
        legal_basis: str = "legitimate_interests",
    ) -> str:
        """Log access to personal data"""
        return self.log_action(
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            action_type="DATA_ACCESS",
            resource_type="personal_data",
            description=f"Accessed data for purpose: {purpose}",
            legal_basis=legal_basis,
            data_categories=data_accessed,
        )

    def log_biometric_processing(
        self,
        actor_user_id: str,
        target_user_id: str,
        processing_type: str,
        consent_verified: bool,
    ) -> str:
        """Log biometric data processing"""
        return self.log_action(
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            action_type="BIOMETRIC_PROCESSING",
            resource_type="biometric_data",
            description=f"Biometric {processing_type} - consent verified: {consent_verified}",
            legal_basis="consent" if consent_verified else "security_monitoring",
            data_categories=["biometric_templates", "facial_features"],
            metadata={
                "processing_type": processing_type,
                "consent_verified": consent_verified,
            },
        )

    def log_data_deletion(
        self,
        actor_user_id: str,
        target_user_id: str,
        data_types: List[str],
        retention_policy: str,
    ) -> str:
        """Log data deletion activity"""
        return self.log_action(
            actor_user_id=actor_user_id,
            target_user_id=target_user_id,
            action_type="DATA_DELETION",
            resource_type="personal_data",
            description=f"Deleted data per retention policy: {retention_policy}",
            legal_basis="retention_policy",
            data_categories=data_types,
            metadata={"retention_policy": retention_policy},
        )

    def log_security_incident(
        self,
        actor_user_id: str,
        incident_type: str,
        affected_users: List[str],
        severity: str,
    ) -> str:
        """Log security incidents affecting personal data"""
        return self.log_action(
            actor_user_id=actor_user_id,
            action_type="SECURITY_INCIDENT",
            resource_type="security_event",
            description=f"Security incident: {incident_type} - severity: {severity}",
            legal_basis="security_monitoring",
            data_categories=["security_logs"],
            metadata={
                "incident_type": incident_type,
                "severity": severity,
                "affected_users_count": len(affected_users),
                "affected_users": affected_users[:10],  # Limit for storage
            },
        )

    def search_audit_logs(
        self,
        target_user_id: Optional[str] = None,
        action_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 1000,
    ) -> List[Dict[str, Any]]:
        """Search audit logs for compliance investigations"""
        try:
            where_clauses = []
            params = []

            if target_user_id:
                where_clauses.append("target_user_id = %s")
                params.append(target_user_id)

            if action_type:
                where_clauses.append("action_type = %s")
                params.append(action_type)

            if start_date:
                where_clauses.append("timestamp >= %s")
                params.append(start_date)

            if end_date:
                where_clauses.append("timestamp <= %s")
                params.append(end_date)

            where_clause = (
                "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
            )

            query_sql = f"""
                SELECT id, timestamp, actor_user_id, target_user_id, action_type,
                       resource_type, resource_id, description, legal_basis,
                       data_categories, metadata
                FROM compliance_audit_log
                {where_clause}
                ORDER BY timestamp DESC
                LIMIT %s
            """

            params.append(limit)
            df = execute_query(self.db, query_sql, tuple(params))

            return df.to_dict("records") if not df.empty else []

        except Exception as e:
            logger.error(f"Failed to search audit logs: {e}")
            return []

    def get_user_audit_trail(
        self, user_id: str, days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get complete audit trail for a specific user (for DSAR requests)"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

            query_sql = """
                SELECT timestamp, action_type, resource_type, description, 
                       legal_basis, data_categories, actor_user_id
                FROM compliance_audit_log
                WHERE (target_user_id = %s OR actor_user_id = %s)
                  AND timestamp >= %s
                ORDER BY timestamp DESC
            """

            df = execute_query(self.db, query_sql, (user_id, user_id, cutoff_date))
            return df.to_dict("records") if not df.empty else []

        except Exception as e:
            logger.error(f"Failed to get user audit trail: {e}")
            return []

    def generate_compliance_report(
        self, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Generate compliance report for regulators"""
        try:
            # Activity summary
            summary_sql = """
                SELECT action_type, COUNT(*) as count
                FROM compliance_audit_log
                WHERE timestamp BETWEEN %s AND %s
                GROUP BY action_type
                ORDER BY count DESC
            """

            summary_df = execute_query(self.db, summary_sql, (start_date, end_date))
            activity_summary = (
                summary_df.to_dict("records") if not summary_df.empty else []
            )

            # Legal basis breakdown
            legal_basis_sql = """
                SELECT legal_basis, COUNT(*) as count
                FROM compliance_audit_log
                WHERE timestamp BETWEEN %s AND %s
                  AND legal_basis IS NOT NULL
                GROUP BY legal_basis
            """

            legal_df = execute_query(self.db, legal_basis_sql, (start_date, end_date))
            legal_basis_summary = (
                legal_df.to_dict("records") if not legal_df.empty else []
            )

            # Data category processing
            data_cat_sql = """
                SELECT data_categories, COUNT(*) as count
                FROM compliance_audit_log
                WHERE timestamp BETWEEN %s AND %s
                  AND data_categories IS NOT NULL
                GROUP BY data_categories
                LIMIT 20
            """

            data_df = execute_query(self.db, data_cat_sql, (start_date, end_date))
            data_categories = data_df.to_dict("records") if not data_df.empty else []

            return {
                "report_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                },
                "activity_summary": activity_summary,
                "legal_basis_breakdown": legal_basis_summary,
                "data_categories_processed": data_categories,
                "total_logged_actions": sum(item["count"] for item in activity_summary),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to generate compliance report: {e}")
            return {
                "error": "Failed to generate compliance report",
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

    def _get_client_ip(self) -> Optional[str]:
        """Get client IP from Flask request context"""
        try:
            # Handle X-Forwarded-For header from proxies
            if request.headers.get("X-Forwarded-For"):
                return request.headers.get("X-Forwarded-For").split(",")[0].strip()
            elif request.headers.get("X-Real-IP"):
                return request.headers.get("X-Real-IP")
            else:
                return request.remote_addr
        except Exception:
            return None

    def _get_user_agent(self) -> Optional[str]:
        """Get user agent from Flask request context"""
        try:
            return request.headers.get("User-Agent")
        except Exception:
            return None

    def _get_request_id(self) -> Optional[str]:
        """Get request ID from Flask g context or generate one"""
        try:
            # Check if request ID already set in Flask g
            if hasattr(g, "request_id"):
                return g.request_id

            # Check for common request ID headers
            request_id = (
                request.headers.get("X-Request-ID")
                or request.headers.get("X-Correlation-ID")
                or request.headers.get("X-Trace-ID")
            )

            if not request_id:
                # Generate a request ID for this request
                request_id = str(uuid4())[:8].upper()
                g.request_id = request_id

            return request_id

        except Exception:
            return str(uuid4())[:8].upper()


# Factory function for DI container
def create_audit_logger(db: DatabaseProtocol) -> ComplianceAuditLogger:
    """Create audit logger instance"""
    return ComplianceAuditLogger(db)
