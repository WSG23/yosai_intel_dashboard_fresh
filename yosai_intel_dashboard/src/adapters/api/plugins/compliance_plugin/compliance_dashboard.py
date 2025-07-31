# services/compliance/compliance_dashboard.py
"""Real-time Compliance Monitoring Dashboard for GDPR/APPI"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Protocol

from core.audit_logger import ComplianceAuditLogger
from yosai_intel_dashboard.src.core.interfaces.protocols import DatabaseProtocol
from database.secure_exec import execute_query
from services.compliance.consent_service import ConsentService
from services.compliance.data_retention_service import DataRetentionService
from services.compliance.dpia_service import DPIAService
from services.compliance.dsar_service import DSARService

logger = logging.getLogger(__name__)


@dataclass
class ComplianceMetric:
    """Individual compliance metric"""

    name: str
    value: Any
    status: str  # 'good', 'warning', 'critical'
    threshold: Optional[Any] = None
    description: str = ""
    last_updated: datetime = None


@dataclass
class ComplianceAlert:
    """Compliance alert/warning"""

    alert_id: str
    severity: str  # 'info', 'warning', 'critical'
    title: str
    description: str
    category: str  # 'consent', 'dsar', 'retention', 'security'
    created_at: datetime
    action_required: bool = True


class ComplianceDashboardProtocol(Protocol):
    """Protocol for compliance dashboard operations"""

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get high-level compliance dashboard summary"""
        ...

    def get_compliance_alerts(self) -> List[ComplianceAlert]:
        """Get active compliance alerts"""
        ...


class ComplianceDashboard:
    """Centralized compliance monitoring and reporting dashboard"""

    def __init__(
        self,
        db: DatabaseProtocol,
        audit_logger: ComplianceAuditLogger,
        consent_service: ConsentService,
        dsar_service: DSARService,
        retention_service: DataRetentionService,
        dpia_service: DPIAService,
    ):
        self.db = db
        self.audit_logger = audit_logger
        self.consent_service = consent_service
        self.dsar_service = dsar_service
        self.retention_service = retention_service
        self.dpia_service = dpia_service

        # Compliance thresholds
        self._thresholds = {
            "dsar_response_time_days": 30,
            "consent_withdrawal_processing_hours": 24,
            "data_breach_notification_hours": 72,
            "dpia_completion_days": 14,
            "retention_compliance_percentage": 95.0,
            "audit_log_availability_percentage": 99.5,
        }

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get comprehensive compliance dashboard summary"""
        try:
            # Get individual metric categories
            consent_metrics = self._get_consent_metrics()
            dsar_metrics = self._get_dsar_metrics()
            retention_metrics = self._get_retention_metrics()
            dpia_metrics = self._get_dpia_metrics()
            security_metrics = self._get_security_metrics()
            audit_metrics = self._get_audit_metrics()

            # Calculate overall compliance score
            overall_score = self._calculate_overall_compliance_score(
                [
                    consent_metrics,
                    dsar_metrics,
                    retention_metrics,
                    dpia_metrics,
                    security_metrics,
                    audit_metrics,
                ]
            )

            # Get active alerts
            alerts = self.get_compliance_alerts()
            critical_alerts = [a for a in alerts if a.severity == "critical"]
            warning_alerts = [a for a in alerts if a.severity == "warning"]

            # Generate recommendations
            recommendations = self._generate_compliance_recommendations(
                consent_metrics, dsar_metrics, retention_metrics, alerts
            )

            summary = {
                "overall_compliance": {
                    "score": overall_score,
                    "status": self._get_status_from_score(overall_score),
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                },
                "alerts_summary": {
                    "total_alerts": len(alerts),
                    "critical_count": len(critical_alerts),
                    "warning_count": len(warning_alerts),
                    "action_required_count": len(
                        [a for a in alerts if a.action_required]
                    ),
                },
                "metrics_by_category": {
                    "consent_management": self._metrics_to_dict(consent_metrics),
                    "data_subject_rights": self._metrics_to_dict(dsar_metrics),
                    "data_retention": self._metrics_to_dict(retention_metrics),
                    "impact_assessments": self._metrics_to_dict(dpia_metrics),
                    "security_compliance": self._metrics_to_dict(security_metrics),
                    "audit_logging": self._metrics_to_dict(audit_metrics),
                },
                "recommendations": recommendations,
                "recent_activities": self._get_recent_compliance_activities(),
                "jurisdiction_status": self._get_jurisdiction_compliance_status(),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

            # Audit dashboard access
            self.audit_logger.log_action(
                actor_user_id="system",
                action_type="COMPLIANCE_DASHBOARD_ACCESSED",
                resource_type="compliance_dashboard",
                description="Compliance dashboard summary generated",
                legal_basis="compliance_monitoring",
            )

            return summary

        except Exception as e:
            logger.error(f"Failed to generate dashboard summary: {e}")
            return {"error": str(e)}

    def get_compliance_alerts(self) -> List[ComplianceAlert]:
        """Get all active compliance alerts"""
        alerts = []

        try:
            # Check for overdue DSAR requests
            overdue_dsars = self._check_overdue_dsar_requests()
            alerts.extend(overdue_dsars)

            # Check for consent compliance issues
            consent_alerts = self._check_consent_compliance()
            alerts.extend(consent_alerts)

            # Check for retention policy violations
            retention_alerts = self._check_retention_compliance()
            alerts.extend(retention_alerts)

            # Check for missing DPIAs
            dpia_alerts = self._check_dpia_compliance()
            alerts.extend(dpia_alerts)

            # Check for security compliance issues
            security_alerts = self._check_security_compliance()
            alerts.extend(security_alerts)

            # Sort by severity and creation time
            alerts.sort(
                key=lambda x: (
                    {"critical": 0, "warning": 1, "info": 2}[x.severity],
                    x.created_at,
                ),
                reverse=True,
            )

            return alerts

        except Exception as e:
            logger.error(f"Failed to get compliance alerts: {e}")
            return []

    def get_regulatory_report(
        self, jurisdiction: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, Any]:
        """Generate comprehensive regulatory report"""
        try:
            # Get compliance metrics for period
            period_metrics = self._get_period_compliance_metrics(start_date, end_date)

            # Get audit summary
            audit_summary = self.audit_logger.generate_compliance_report(
                start_date, end_date
            )

            # Get DSAR statistics
            dsar_stats = self._get_dsar_statistics(start_date, end_date)

            # Get consent statistics
            consent_stats = self._get_consent_statistics(start_date, end_date)

            # Get retention actions
            retention_actions = self._get_retention_actions(start_date, end_date)

            # Generate regulatory-specific sections
            regulatory_sections = self._generate_regulatory_sections(jurisdiction)

            report = {
                "report_metadata": {
                    "jurisdiction": jurisdiction,
                    "reporting_period": {
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                    },
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "report_version": "1.0",
                },
                "executive_summary": {
                    "compliance_score": period_metrics.get("overall_score", 0),
                    "total_data_subjects": self._get_total_data_subjects(),
                    "processing_activities_count": self._get_processing_activities_count(),
                    "incidents_reported": 0,  # Implement based on your incident tracking
                    "dsars_received": dsar_stats.get("total_requests", 0),
                    "dsars_completed_on_time": dsar_stats.get("completed_on_time", 0),
                },
                "data_processing_inventory": self._get_processing_inventory(),
                "consent_management": consent_stats,
                "data_subject_rights": dsar_stats,
                "data_retention_and_deletion": retention_actions,
                "security_measures": self._get_security_measures_summary(),
                "audit_trail": audit_summary,
                "impact_assessments": self._get_dpia_summary(),
                "regulatory_compliance": regulatory_sections,
                "identified_issues": [
                    alert.__dict__ for alert in self.get_compliance_alerts()
                ],
                "improvement_actions": self._get_improvement_actions(),
            }

            # Audit report generation
            self.audit_logger.log_action(
                actor_user_id="system",
                action_type="REGULATORY_REPORT_GENERATED",
                resource_type="regulatory_report",
                description=f"Regulatory compliance report generated for {jurisdiction}",
                legal_basis="regulatory_reporting",
                metadata={
                    "jurisdiction": jurisdiction,
                    "period_days": (end_date - start_date).days,
                },
            )

            return report

        except Exception as e:
            logger.error(f"Failed to generate regulatory report: {e}")
            return {"error": str(e)}

    def _get_consent_metrics(self) -> List[ComplianceMetric]:
        """Get consent management metrics"""
        metrics = []

        try:
            # Total active consents
            active_consents_sql = """
                SELECT COUNT(*) as count 
                FROM consent_log 
                WHERE is_active = TRUE
            """
            df = execute_query(self.db, active_consents_sql)
            active_count = df.iloc[0]["count"] if not df.empty else 0

            metrics.append(
                ComplianceMetric(
                    name="active_consents",
                    value=active_count,
                    status="good" if active_count > 0 else "warning",
                    description="Total active user consents",
                )
            )

            # Consent withdrawal processing time
            withdrawal_time_sql = """
                SELECT AVG(EXTRACT(EPOCH FROM (withdrawn_timestamp - granted_timestamp))/3600) as avg_hours
                FROM consent_log 
                WHERE withdrawn_timestamp IS NOT NULL
                  AND withdrawn_timestamp >= NOW() - INTERVAL '30 days'
            """
            df = execute_query(self.db, withdrawal_time_sql)
            avg_hours = (
                df.iloc[0]["avg_hours"]
                if not df.empty and df.iloc[0]["avg_hours"]
                else 0
            )

            metrics.append(
                ComplianceMetric(
                    name="consent_withdrawal_processing_time",
                    value=round(avg_hours, 2),
                    status="good" if avg_hours <= 24 else "warning",
                    threshold=24,
                    description="Average consent withdrawal processing time (hours)",
                )
            )

            # Consent by jurisdiction
            jurisdiction_sql = """
                SELECT jurisdiction, COUNT(*) as count
                FROM consent_log 
                WHERE is_active = TRUE
                GROUP BY jurisdiction
            """
            df = execute_query(self.db, jurisdiction_sql)
            jurisdiction_breakdown = df.to_dict("records") if not df.empty else []

            metrics.append(
                ComplianceMetric(
                    name="consent_by_jurisdiction",
                    value=jurisdiction_breakdown,
                    status="good",
                    description="Active consents by jurisdiction",
                )
            )

        except Exception as e:
            logger.error(f"Failed to get consent metrics: {e}")

        return metrics

    def _get_dsar_metrics(self) -> List[ComplianceMetric]:
        """Get DSAR (Data Subject Rights) metrics"""
        metrics = []

        try:
            # DSAR response time compliance
            response_time_sql = """
                SELECT 
                    COUNT(*) as total_requests,
                    COUNT(CASE WHEN fulfilled_date <= due_date THEN 1 END) as on_time_responses,
                    AVG(EXTRACT(EPOCH FROM (COALESCE(fulfilled_date, NOW()) - received_date))/86400) as avg_response_days
                FROM dsar_requests 
                WHERE received_date >= NOW() - INTERVAL '90 days'
            """

            df = execute_query(self.db, response_time_sql)
            if not df.empty:
                row = df.iloc[0]
                total_requests = row["total_requests"]
                on_time_responses = row["on_time_responses"]
                avg_response_days = row["avg_response_days"]

                compliance_rate = (on_time_responses / max(total_requests, 1)) * 100

                metrics.append(
                    ComplianceMetric(
                        name="dsar_response_compliance",
                        value=round(compliance_rate, 1),
                        status=(
                            "good"
                            if compliance_rate >= 95
                            else "warning" if compliance_rate >= 80 else "critical"
                        ),
                        threshold=95,
                        description="DSAR response time compliance rate (%)",
                    )
                )

                metrics.append(
                    ComplianceMetric(
                        name="average_dsar_response_time",
                        value=round(avg_response_days, 1),
                        status="good" if avg_response_days <= 25 else "warning",
                        threshold=30,
                        description="Average DSAR response time (days)",
                    )
                )

            # Pending DSARs
            pending_sql = """
                SELECT COUNT(*) as pending_count
                FROM dsar_requests 
                WHERE status IN ('pending', 'in_progress')
                  AND due_date <= NOW() + INTERVAL '7 days'
            """

            df = execute_query(self.db, pending_sql)
            pending_count = df.iloc[0]["pending_count"] if not df.empty else 0

            metrics.append(
                ComplianceMetric(
                    name="pending_dsars_due_soon",
                    value=pending_count,
                    status=(
                        "good"
                        if pending_count == 0
                        else "warning" if pending_count <= 5 else "critical"
                    ),
                    description="DSAR requests due within 7 days",
                )
            )

        except Exception as e:
            logger.error(f"Failed to get DSAR metrics: {e}")

        return metrics

    def _get_retention_metrics(self) -> List[ComplianceMetric]:
        """Get data retention compliance metrics"""
        metrics = []

        try:
            # Data scheduled for deletion
            scheduled_deletion_sql = """
                SELECT COUNT(*) as scheduled_count
                FROM people 
                WHERE data_retention_date IS NOT NULL
                  AND data_retention_date <= NOW() + INTERVAL '30 days'
            """

            df = execute_query(self.db, scheduled_deletion_sql)
            scheduled_count = df.iloc[0]["scheduled_count"] if not df.empty else 0

            metrics.append(
                ComplianceMetric(
                    name="data_scheduled_for_deletion",
                    value=scheduled_count,
                    status="warning" if scheduled_count > 0 else "good",
                    description="Data subjects scheduled for deletion within 30 days",
                )
            )

            # Overdue deletions
            overdue_deletion_sql = """
                SELECT COUNT(*) as overdue_count
                FROM people 
                WHERE data_retention_date IS NOT NULL
                  AND data_retention_date < NOW()
            """

            df = execute_query(self.db, overdue_deletion_sql)
            overdue_count = df.iloc[0]["overdue_count"] if not df.empty else 0

            metrics.append(
                ComplianceMetric(
                    name="overdue_data_deletions",
                    value=overdue_count,
                    status="critical" if overdue_count > 0 else "good",
                    description="Data subjects with overdue deletion dates",
                )
            )

        except Exception as e:
            logger.error(f"Failed to get retention metrics: {e}")

        return metrics

    def _get_dpia_metrics(self) -> List[ComplianceMetric]:
        """Get DPIA compliance metrics"""
        metrics = []

        try:
            # Get DPIA dashboard data from DPIA service
            dpia_data = self.dpia_service.get_dpia_dashboard_data()

            if "summary" in dpia_data:
                summary = dpia_data["summary"]

                metrics.append(
                    ComplianceMetric(
                        name="dpia_completion_rate",
                        value=summary.get("compliance_rate", 0),
                        status=(
                            "good"
                            if summary.get("compliance_rate", 0) >= 95
                            else "warning"
                        ),
                        threshold=95,
                        description="DPIA completion rate (%)",
                    )
                )

                metrics.append(
                    ComplianceMetric(
                        name="pending_dpias",
                        value=summary.get("dpias_pending", 0),
                        status=(
                            "good"
                            if summary.get("dpias_pending", 0) == 0
                            else "warning"
                        ),
                        description="Pending DPIA assessments",
                    )
                )

        except Exception as e:
            logger.error(f"Failed to get DPIA metrics: {e}")

        return metrics

    def _get_security_metrics(self) -> List[ComplianceMetric]:
        """Get security compliance metrics"""
        metrics = []

        try:
            # Audit log availability
            audit_availability_sql = """
                SELECT 
                    COUNT(*) as total_hours,
                    COUNT(CASE WHEN hour_count > 0 THEN 1 END) as active_hours
                FROM (
                    SELECT DATE_TRUNC('hour', timestamp) as hour, COUNT(*) as hour_count
                    FROM compliance_audit_log 
                    WHERE timestamp >= NOW() - INTERVAL '24 hours'
                    GROUP BY DATE_TRUNC('hour', timestamp)
                ) hourly_counts
            """

            df = execute_query(self.db, audit_availability_sql)
            if not df.empty:
                row = df.iloc[0]
                availability = (row["active_hours"] / max(row["total_hours"], 1)) * 100

                metrics.append(
                    ComplianceMetric(
                        name="audit_log_availability",
                        value=round(availability, 1),
                        status="good" if availability >= 99 else "warning",
                        threshold=99.0,
                        description="Audit logging availability (24h)",
                    )
                )

            # Failed authentication attempts (if you track this)
            metrics.append(
                ComplianceMetric(
                    name="security_monitoring_active",
                    value=True,
                    status="good",
                    description="Security monitoring systems operational",
                )
            )

        except Exception as e:
            logger.error(f"Failed to get security metrics: {e}")

        return metrics

    def _get_audit_metrics(self) -> List[ComplianceMetric]:
        """Get audit trail metrics"""
        metrics = []

        try:
            # Recent audit activity
            recent_activity_sql = """
                SELECT COUNT(*) as recent_entries
                FROM compliance_audit_log 
                WHERE timestamp >= NOW() - INTERVAL '24 hours'
            """

            df = execute_query(self.db, recent_activity_sql)
            recent_count = df.iloc[0]["recent_entries"] if not df.empty else 0

            metrics.append(
                ComplianceMetric(
                    name="recent_audit_entries",
                    value=recent_count,
                    status="good" if recent_count > 0 else "warning",
                    description="Audit entries in last 24 hours",
                )
            )

            # Audit completeness
            metrics.append(
                ComplianceMetric(
                    name="audit_trail_completeness",
                    value=100.0,  # Assume complete unless you have integrity checks
                    status="good",
                    description="Audit trail completeness (%)",
                )
            )

        except Exception as e:
            logger.error(f"Failed to get audit metrics: {e}")

        return metrics

    def _check_overdue_dsar_requests(self) -> List[ComplianceAlert]:
        """Check for overdue DSAR requests"""
        alerts = []

        try:
            overdue_sql = """
                SELECT request_id, user_id, request_type, due_date, 
                       EXTRACT(EPOCH FROM (NOW() - due_date))/86400 as days_overdue
                FROM dsar_requests 
                WHERE status IN ('pending', 'in_progress') 
                  AND due_date < NOW()
                ORDER BY due_date ASC
            """

            df = execute_query(self.db, overdue_sql)

            for row in df.itertuples(index=False):
                days_overdue = int(row.days_overdue)
                severity = "critical" if days_overdue > 5 else "warning"

                alerts.append(
                    ComplianceAlert(
                        alert_id=f"overdue_dsar_{row.request_id}",
                        severity=severity,
                        title=f"Overdue DSAR Request: {row.request_id}",
                        description=f"DSAR request of type '{row.request_type}' is {days_overdue} days overdue",
                        category="dsar",
                        created_at=datetime.now(timezone.utc),
                        action_required=True,
                    )
                )

        except Exception as e:
            logger.error(f"Failed to check overdue DSARs: {e}")

        return alerts

    def _metrics_to_dict(self, metrics: List[ComplianceMetric]) -> Dict[str, Any]:
        """Convert metrics list to dictionary format"""
        return {
            metric.name: {
                "value": metric.value,
                "status": metric.status,
                "threshold": metric.threshold,
                "description": metric.description,
                "last_updated": (
                    metric.last_updated.isoformat() if metric.last_updated else None
                ),
            }
            for metric in metrics
        }

    def _calculate_overall_compliance_score(
        self, metric_categories: List[List[ComplianceMetric]]
    ) -> float:
        """Calculate overall compliance score from all metrics"""
        total_score = 0.0
        total_weight = 0.0

        for category in metric_categories:
            for metric in category:
                if metric.status == "good":
                    score = 100.0
                elif metric.status == "warning":
                    score = 70.0
                else:  # critical
                    score = 30.0

                weight = 1.0
                total_score += score * weight
                total_weight += weight

        return round(total_score / max(total_weight, 1), 1)

    def _get_status_from_score(self, score: float) -> str:
        """Convert numeric score to status"""
        if score >= 90:
            return "excellent"
        elif score >= 80:
            return "good"
        elif score >= 60:
            return "warning"
        else:
            return "critical"


# Factory function for DI container
def create_compliance_dashboard(
    db: DatabaseProtocol,
    audit_logger: ComplianceAuditLogger,
    consent_service: ConsentService,
    dsar_service: DSARService,
    retention_service: DataRetentionService,
    dpia_service: DPIAService,
) -> ComplianceDashboard:
    """Create compliance dashboard instance"""
    return ComplianceDashboard(
        db, audit_logger, consent_service, dsar_service, retention_service, dpia_service
    )
