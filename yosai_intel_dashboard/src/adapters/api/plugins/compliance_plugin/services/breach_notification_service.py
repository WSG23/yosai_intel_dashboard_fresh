# services/compliance/breach_notification_service.py
"""Data Breach Notification Service for GDPR Article 33/34 Compliance"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol
from uuid import uuid4

from core.audit_logger import ComplianceAuditLogger
from yosai_intel_dashboard.src.core.interfaces.protocols import DatabaseProtocol
from core.unicode import safe_unicode_encode
from database.secure_exec import execute_command, execute_query

logger = logging.getLogger(__name__)


class BreachSeverity(Enum):
    """Data breach severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class BreachCategory(Enum):
    """Types of data breaches"""

    CONFIDENTIALITY_BREACH = "confidentiality_breach"  # Unauthorized access/disclosure
    INTEGRITY_BREACH = "integrity_breach"  # Data alteration/corruption
    AVAILABILITY_BREACH = "availability_breach"  # Data loss/destruction
    COMBINED_BREACH = "combined_breach"  # Multiple categories


class NotificationStatus(Enum):
    """Breach notification status"""

    DETECTED = "detected"
    UNDER_INVESTIGATION = "under_investigation"
    SUPERVISOR_NOTIFIED = "supervisor_notified"
    INDIVIDUALS_NOTIFIED = "individuals_notified"
    RESOLVED = "resolved"
    CLOSED = "closed"


class BreachNotificationServiceProtocol(Protocol):
    """Protocol for breach notification operations"""

    def report_breach(self, breach_data: Dict[str, Any]) -> str:
        """Report a new data breach"""
        ...

    def assess_notification_requirements(self, breach_id: str) -> Dict[str, Any]:
        """Assess if breach requires notification to authorities/individuals"""
        ...


class BreachNotificationService:
    """Manages data breach detection, assessment, and notification workflows"""

    def __init__(self, db: DatabaseProtocol, audit_logger: ComplianceAuditLogger):
        self.db = db
        self.audit_logger = audit_logger

        # GDPR notification timeframes
        self._notification_deadlines = {
            "supervisor_hours": 72,  # GDPR Article 33 - 72 hours to DPA
            "individual_days": 30,  # GDPR Article 34 - without undue delay
            "documentation_hours": 24,  # Internal documentation requirement
        }

        # Risk assessment criteria
        self._high_risk_indicators = {
            "data_types": [
                "biometric_templates",
                "health_data",
                "genetic_data",
                "criminal_conviction_data",
                "financial_data",
                "children_data",
            ],
            "affected_count_threshold": 1000,
            "geographic_scope_eu": True,
            "identity_theft_risk": True,
            "financial_loss_risk": True,
            "discrimination_risk": True,
        }

    def report_breach(
        self,
        breach_description: str,
        affected_data_types: List[str],
        estimated_affected_individuals: int,
        detection_timestamp: datetime,
        breach_category: BreachCategory,
        initial_assessment: Dict[str, Any],
        detected_by: str,
        containment_measures: List[str] = None,
    ) -> str:
        """
        Report a new data breach and initiate notification workflow

        Returns:
            str: Breach incident ID
        """
        try:
            breach_id = (
                f"BREACH-{datetime.now().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}"
            )

            # Calculate severity and risk level
            severity = self._assess_breach_severity(
                affected_data_types, estimated_affected_individuals, initial_assessment
            )

            # Determine notification requirements
            notification_requirements = self._determine_notification_requirements(
                severity,
                affected_data_types,
                estimated_affected_individuals,
                initial_assessment,
            )

            # Calculate notification deadlines
            deadlines = self._calculate_notification_deadlines(detection_timestamp)

            # Create breach record
            breach_record = {
                "breach_id": breach_id,
                "description": safe_unicode_encode(breach_description),
                "breach_category": breach_category.value,
                "severity": severity.value,
                "detection_timestamp": detection_timestamp,
                "reported_timestamp": datetime.now(timezone.utc),
                "detected_by": detected_by,
                "affected_data_types": affected_data_types,
                "estimated_affected_individuals": estimated_affected_individuals,
                "initial_assessment": initial_assessment,
                "containment_measures": containment_measures or [],
                "notification_requirements": notification_requirements,
                "notification_deadlines": deadlines,
                "status": NotificationStatus.DETECTED.value,
                "supervisor_notification_required": notification_requirements.get(
                    "supervisor_required", False
                ),
                "individual_notification_required": notification_requirements.get(
                    "individuals_required", False
                ),
                "created_at": datetime.now(timezone.utc),
            }

            # Store breach record
            self._store_breach_record(breach_record)

            # Audit the breach report
            self.audit_logger.log_action(
                actor_user_id=detected_by,
                action_type="DATA_BREACH_REPORTED",
                resource_type="data_breach",
                resource_id=breach_id,
                description=f"Data breach reported: {severity.value} severity, {estimated_affected_individuals} affected",
                legal_basis="breach_notification_obligation",
                data_categories=affected_data_types,
                metadata={
                    "breach_category": breach_category.value,
                    "severity": severity.value,
                    "supervisor_notification_required": notification_requirements.get(
                        "supervisor_required"
                    ),
                    "notification_deadline_hours": deadlines.get(
                        "supervisor_notification_deadline_hours"
                    ),
                },
            )

            # Trigger immediate actions if high severity
            if severity in [BreachSeverity.HIGH, BreachSeverity.CRITICAL]:
                self._trigger_emergency_response(breach_id, breach_record)

            logger.info(
                f"Data breach reported: {breach_id}, severity: {severity.value}"
            )
            return breach_id

        except Exception as e:
            logger.error(f"Failed to report breach: {e}")
            raise

    def assess_notification_requirements(self, breach_id: str) -> Dict[str, Any]:
        """Assess and update notification requirements for a breach"""
        try:
            breach_record = self._get_breach_record(breach_id)
            if not breach_record:
                return {"error": "Breach not found"}

            # Re-assess with updated information
            severity = BreachSeverity(breach_record["severity"])
            affected_data_types = breach_record["affected_data_types"]
            estimated_affected = breach_record["estimated_affected_individuals"]
            assessment = breach_record.get(
                "updated_assessment", breach_record.get("initial_assessment", {})
            )

            # Detailed risk assessment
            risk_assessment = self._conduct_detailed_risk_assessment(
                severity, affected_data_types, estimated_affected, assessment
            )

            # Update notification requirements
            notification_requirements = self._determine_notification_requirements(
                severity, affected_data_types, estimated_affected, assessment
            )

            # Check if deadlines are approaching
            deadlines_status = self._check_notification_deadlines(breach_record)

            assessment_result = {
                "breach_id": breach_id,
                "current_severity": severity.value,
                "risk_assessment": risk_assessment,
                "notification_requirements": notification_requirements,
                "deadlines_status": deadlines_status,
                "recommended_actions": self._recommend_immediate_actions(
                    risk_assessment, notification_requirements, deadlines_status
                ),
                "assessment_timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Update breach record with new assessment
            self._update_breach_assessment(breach_id, assessment_result)

            # Audit the assessment
            self.audit_logger.log_action(
                actor_user_id="system",
                action_type="BREACH_ASSESSMENT_UPDATED",
                resource_type="data_breach",
                resource_id=breach_id,
                description="Breach notification requirements assessed",
                legal_basis="breach_notification_obligation",
                metadata=risk_assessment,
            )

            return assessment_result

        except Exception as e:
            logger.error(f"Failed to assess breach {breach_id}: {e}")
            return {"error": str(e)}

    def notify_supervisory_authority(
        self, breach_id: str, notification_details: Dict[str, Any], notified_by: str
    ) -> bool:
        """Record notification to supervisory authority (DPA)"""
        try:
            breach_record = self._get_breach_record(breach_id)
            if not breach_record:
                logger.error(
                    f"Breach {breach_id} not found for supervisor notification"
                )
                return False

            # Validate notification is within deadline
            detection_time = breach_record["detection_timestamp"]
            if isinstance(detection_time, str):
                detection_time = datetime.fromisoformat(
                    detection_time.replace("Z", "+00:00")
                )

            hours_since_detection = (
                datetime.now(timezone.utc) - detection_time
            ).total_seconds() / 3600
            within_deadline = (
                hours_since_detection
                <= self._notification_deadlines["supervisor_hours"]
            )

            # Create notification record
            notification_record = {
                "notification_id": str(uuid4()),
                "breach_id": breach_id,
                "notification_type": "supervisory_authority",
                "recipient": notification_details.get(
                    "authority_name", "Data Protection Authority"
                ),
                "notification_timestamp": datetime.now(timezone.utc),
                "notification_method": notification_details.get(
                    "method", "online_portal"
                ),
                "reference_number": notification_details.get("reference_number"),
                "within_deadline": within_deadline,
                "hours_since_detection": round(hours_since_detection, 2),
                "notified_by": notified_by,
                "notification_content": notification_details,
                "created_at": datetime.now(timezone.utc),
            }

            # Store notification record
            self._store_notification_record(notification_record)

            # Update breach status
            self._update_breach_status(
                breach_id, NotificationStatus.SUPERVISOR_NOTIFIED
            )

            # Audit the notification
            self.audit_logger.log_action(
                actor_user_id=notified_by,
                action_type="SUPERVISOR_AUTHORITY_NOTIFIED",
                resource_type="data_breach",
                resource_id=breach_id,
                description=f'Supervisory authority notified {"within" if within_deadline else "after"} 72-hour deadline',
                legal_basis="breach_notification_obligation",
                metadata={
                    "within_deadline": within_deadline,
                    "hours_since_detection": hours_since_detection,
                    "authority": notification_details.get("authority_name"),
                },
            )

            logger.info(f"Supervisory authority notified for breach {breach_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to record supervisor notification: {e}")
            return False

    def notify_affected_individuals(
        self,
        breach_id: str,
        notification_method: str,
        affected_user_ids: List[str],
        notification_content: str,
        notified_by: str,
    ) -> bool:
        """Record notification to affected individuals"""
        try:
            # Create individual notification records
            notification_id = str(uuid4())

            for user_id in affected_user_ids:
                individual_notification = {
                    "notification_id": f"{notification_id}_{user_id}",
                    "breach_id": breach_id,
                    "notification_type": "affected_individual",
                    "recipient_user_id": user_id,
                    "notification_timestamp": datetime.now(timezone.utc),
                    "notification_method": notification_method,
                    "notification_content": safe_unicode_encode(notification_content),
                    "notified_by": notified_by,
                    "created_at": datetime.now(timezone.utc),
                }

                self._store_notification_record(individual_notification)

            # Update breach status
            self._update_breach_status(
                breach_id, NotificationStatus.INDIVIDUALS_NOTIFIED
            )

            # Audit the individual notifications
            self.audit_logger.log_action(
                actor_user_id=notified_by,
                action_type="AFFECTED_INDIVIDUALS_NOTIFIED",
                resource_type="data_breach",
                resource_id=breach_id,
                description=f"Notified {len(affected_user_ids)} affected individuals via {notification_method}",
                legal_basis="breach_notification_obligation",
                metadata={
                    "affected_count": len(affected_user_ids),
                    "notification_method": notification_method,
                },
            )

            logger.info(
                f"Notified {len(affected_user_ids)} individuals for breach {breach_id}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to record individual notifications: {e}")
            return False

    def get_breach_dashboard_data(self) -> Dict[str, Any]:
        """Get breach monitoring dashboard data"""
        try:
            # Get recent breaches
            recent_breaches_sql = """
                SELECT breach_id, severity, status, detection_timestamp, 
                       estimated_affected_individuals, supervisor_notification_required
                FROM data_breaches 
                WHERE detection_timestamp >= NOW() - INTERVAL '90 days'
                ORDER BY detection_timestamp DESC
            """

            df = execute_query(self.db, recent_breaches_sql)
            recent_breaches = df.to_dict("records") if not df.empty else []

            # Calculate summary metrics
            total_breaches = len(recent_breaches)
            high_severity_count = len(
                [b for b in recent_breaches if b["severity"] in ["high", "critical"]]
            )

            # Check notification compliance
            overdue_notifications = self._get_overdue_notifications()

            # Get breach statistics by category
            breach_stats = self._get_breach_statistics()

            return {
                "summary": {
                    "total_breaches_90d": total_breaches,
                    "high_severity_breaches": high_severity_count,
                    "overdue_notifications": len(overdue_notifications),
                    "notification_compliance_rate": self._calculate_notification_compliance_rate(),
                },
                "recent_breaches": recent_breaches,
                "overdue_notifications": overdue_notifications,
                "breach_statistics": breach_stats,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get breach dashboard data: {e}")
            return {"error": str(e)}

    def _assess_breach_severity(
        self,
        affected_data_types: List[str],
        estimated_affected: int,
        assessment: Dict[str, Any],
    ) -> BreachSeverity:
        """Assess breach severity based on impact factors"""
        severity_score = 0

        # Data type sensitivity scoring
        for data_type in affected_data_types:
            if data_type in self._high_risk_indicators["data_types"]:
                severity_score += 20
            elif data_type in ["access_logs", "employee_data"]:
                severity_score += 10
            else:
                severity_score += 5

        # Scale impact
        if estimated_affected >= 10000:
            severity_score += 30
        elif estimated_affected >= 1000:
            severity_score += 20
        elif estimated_affected >= 100:
            severity_score += 10
        else:
            severity_score += 5

        # Assessment factors
        if assessment.get("identity_theft_risk", False):
            severity_score += 25
        if assessment.get("financial_loss_risk", False):
            severity_score += 20
        if assessment.get("discrimination_risk", False):
            severity_score += 15
        if assessment.get("children_affected", False):
            severity_score += 20

        # Determine severity level
        if severity_score >= 80:
            return BreachSeverity.CRITICAL
        elif severity_score >= 60:
            return BreachSeverity.HIGH
        elif severity_score >= 40:
            return BreachSeverity.MEDIUM
        else:
            return BreachSeverity.LOW

    def _determine_notification_requirements(
        self,
        severity: BreachSeverity,
        affected_data_types: List[str],
        estimated_affected: int,
        assessment: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Determine notification requirements per GDPR Articles 33/34"""

        # GDPR Article 33 - Notification to supervisory authority
        # Required unless "unlikely to result in a risk to rights and freedoms"
        supervisor_required = (
            severity
            in [BreachSeverity.MEDIUM, BreachSeverity.HIGH, BreachSeverity.CRITICAL]
            or estimated_affected >= 100
            or any(
                dt in self._high_risk_indicators["data_types"]
                for dt in affected_data_types
            )
        )

        # GDPR Article 34 - Notification to individuals
        # Required if "likely to result in high risk to rights and freedoms"
        individuals_required = (
            severity in [BreachSeverity.HIGH, BreachSeverity.CRITICAL]
            or assessment.get("identity_theft_risk", False)
            or assessment.get("financial_loss_risk", False)
            or assessment.get("discrimination_risk", False)
            or (
                estimated_affected >= 1000
                and any(
                    dt in self._high_risk_indicators["data_types"]
                    for dt in affected_data_types
                )
            )
        )

        return {
            "supervisor_required": supervisor_required,
            "individuals_required": individuals_required,
            "supervisor_deadline_hours": 72,
            "individuals_deadline_description": "without undue delay",
            "justification": self._generate_notification_justification(
                supervisor_required, individuals_required, severity, assessment
            ),
        }

    def _calculate_notification_deadlines(
        self, detection_timestamp: datetime
    ) -> Dict[str, Any]:
        """Calculate notification deadlines from detection time"""
        supervisor_deadline = detection_timestamp + timedelta(
            hours=self._notification_deadlines["supervisor_hours"]
        )

        documentation_deadline = detection_timestamp + timedelta(
            hours=self._notification_deadlines["documentation_hours"]
        )

        return {
            "detection_timestamp": detection_timestamp.isoformat(),
            "supervisor_notification_deadline": supervisor_deadline.isoformat(),
            "supervisor_notification_deadline_hours": self._notification_deadlines[
                "supervisor_hours"
            ],
            "documentation_deadline": documentation_deadline.isoformat(),
            "individual_notification_deadline": "As soon as reasonably feasible",
        }

    def _conduct_detailed_risk_assessment(
        self,
        severity: BreachSeverity,
        affected_data_types: List[str],
        estimated_affected: int,
        assessment: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Conduct detailed risk assessment for the breach"""

        # Risk to rights and freedoms analysis
        rights_impact = {
            "privacy_impact": (
                "High"
                if any(
                    dt in ["biometric_templates", "health_data"]
                    for dt in affected_data_types
                )
                else "Medium"
            ),
            "autonomy_impact": (
                "Medium"
                if assessment.get("automated_decision_making", False)
                else "Low"
            ),
            "discrimination_risk": (
                "High" if assessment.get("discrimination_risk", False) else "Low"
            ),
            "identity_theft_risk": (
                "High" if assessment.get("identity_theft_risk", False) else "Medium"
            ),
            "financial_loss_risk": (
                "High" if assessment.get("financial_loss_risk", False) else "Low"
            ),
        }

        # Likelihood assessment
        likelihood_factors = {
            "data_accessibility": assessment.get("data_accessibility", "encrypted"),
            "attacker_motivation": assessment.get("attacker_motivation", "unknown"),
            "technical_barriers": assessment.get("technical_barriers", "strong"),
            "containment_effectiveness": assessment.get(
                "containment_effectiveness", "effective"
            ),
        }

        # Overall risk level
        high_impact_count = sum(
            1 for impact in rights_impact.values() if impact == "High"
        )
        overall_risk = (
            "High"
            if high_impact_count >= 2
            else "Medium" if high_impact_count >= 1 else "Low"
        )

        return {
            "overall_risk_level": overall_risk,
            "rights_and_freedoms_impact": rights_impact,
            "likelihood_factors": likelihood_factors,
            "estimated_affected_individuals": estimated_affected,
            "data_sensitivity_assessment": {
                dt: (
                    "High"
                    if dt in self._high_risk_indicators["data_types"]
                    else "Medium"
                )
                for dt in affected_data_types
            },
            "mitigation_factors": assessment.get("mitigation_factors", []),
            "assessment_confidence": assessment.get("assessment_confidence", "medium"),
        }

    def _store_breach_record(self, breach_record: Dict[str, Any]) -> None:
        """Store breach record in database"""
        try:
            insert_sql = """
                INSERT INTO data_breaches 
                (breach_id, description, breach_category, severity, detection_timestamp,
                 reported_timestamp, detected_by, affected_data_types, estimated_affected_individuals,
                 initial_assessment, containment_measures, notification_requirements,
                 notification_deadlines, status, supervisor_notification_required,
                 individual_notification_required, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

            import json

            execute_command(
                self.db,
                insert_sql,
                (
                    breach_record["breach_id"],
                    breach_record["description"],
                    breach_record["breach_category"],
                    breach_record["severity"],
                    breach_record["detection_timestamp"],
                    breach_record["reported_timestamp"],
                    breach_record["detected_by"],
                    json.dumps(breach_record["affected_data_types"]),
                    breach_record["estimated_affected_individuals"],
                    json.dumps(breach_record["initial_assessment"]),
                    json.dumps(breach_record["containment_measures"]),
                    json.dumps(breach_record["notification_requirements"]),
                    json.dumps(breach_record["notification_deadlines"]),
                    breach_record["status"],
                    breach_record["supervisor_notification_required"],
                    breach_record["individual_notification_required"],
                    breach_record["created_at"],
                ),
            )

        except Exception as e:
            logger.error(f"Failed to store breach record: {e}")
            raise


# Factory function for DI container
def create_breach_notification_service(
    db: DatabaseProtocol, audit_logger: ComplianceAuditLogger
) -> BreachNotificationService:
    """Create breach notification service instance"""
    return BreachNotificationService(db, audit_logger)


# Database schema for breach notification tables
BREACH_NOTIFICATION_TABLES_SQL = """
-- Data Breach Notification Tables

CREATE TABLE IF NOT EXISTS data_breaches (
    breach_id VARCHAR(50) PRIMARY KEY,
    description TEXT NOT NULL,
    breach_category VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    detection_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    reported_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    detected_by VARCHAR(50) NOT NULL,
    affected_data_types JSONB NOT NULL,
    estimated_affected_individuals INTEGER NOT NULL,
    initial_assessment JSONB,
    updated_assessment JSONB,
    containment_measures JSONB,
    notification_requirements JSONB,
    notification_deadlines JSONB,
    status VARCHAR(30) NOT NULL DEFAULT 'detected',
    supervisor_notification_required BOOLEAN NOT NULL DEFAULT FALSE,
    individual_notification_required BOOLEAN NOT NULL DEFAULT FALSE,
    resolution_timestamp TIMESTAMP WITH TIME ZONE,
    lessons_learned TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_data_breaches_detection_timestamp ON data_breaches(detection_timestamp);
CREATE INDEX IF NOT EXISTS idx_data_breaches_severity ON data_breaches(severity);
CREATE INDEX IF NOT EXISTS idx_data_breaches_status ON data_breaches(status);

CREATE TABLE IF NOT EXISTS breach_notifications (
    notification_id VARCHAR(50) PRIMARY KEY,
    breach_id VARCHAR(50) REFERENCES data_breaches(breach_id),
    notification_type VARCHAR(30) NOT NULL,
    recipient VARCHAR(200),
    recipient_user_id VARCHAR(50),
    notification_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    notification_method VARCHAR(50) NOT NULL,
    reference_number VARCHAR(100),
    within_deadline BOOLEAN,
    hours_since_detection NUMERIC(10,2),
    notification_content TEXT,
    notified_by VARCHAR(50) NOT NULL,
    delivery_status VARCHAR(20) DEFAULT 'sent',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_breach_notifications_breach_id ON breach_notifications(breach_id);
CREATE INDEX IF NOT EXISTS idx_breach_notifications_type ON breach_notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_breach_notifications_timestamp ON breach_notifications(notification_timestamp);

-- Trigger for updating breach updated_at timestamp
CREATE OR REPLACE FUNCTION update_breach_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_breach_updated_at
    BEFORE UPDATE ON data_breaches
    FOR EACH ROW
    EXECUTE FUNCTION update_breach_updated_at();
"""
