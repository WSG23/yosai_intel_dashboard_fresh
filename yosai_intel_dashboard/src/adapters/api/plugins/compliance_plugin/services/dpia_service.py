# services/compliance/dpia_service.py
"""Data Protection Impact Assessment (DPIA) Service for GDPR Article 35"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol
from uuid import uuid4

from yosai_intel_dashboard.src.core.audit_logger import ComplianceAuditLogger
from yosai_intel_dashboard.src.core.interfaces.protocols import DatabaseProtocol
from database.secure_exec import execute_command, execute_query

logger = logging.getLogger(__name__)


class DPIATrigger(Enum):
    """DPIA trigger criteria per GDPR Article 35"""

    SYSTEMATIC_MONITORING = "systematic_monitoring"
    SPECIAL_CATEGORY_DATA = "special_category_data"
    LARGE_SCALE_PROCESSING = "large_scale_processing"
    BIOMETRIC_IDENTIFICATION = "biometric_identification"
    AUTOMATED_DECISION_MAKING = "automated_decision_making"
    VULNERABLE_POPULATIONS = "vulnerable_populations"
    INNOVATIVE_TECHNOLOGY = "innovative_technology"
    DATA_MATCHING = "data_matching"
    PUBLIC_AREA_MONITORING = "public_area_monitoring"


class RiskLevel(Enum):
    """Risk assessment levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DPIAServiceProtocol(Protocol):
    """Protocol for DPIA operations"""

    def assess_processing_activity(
        self, activity_name: str, data_types: List[str]
    ) -> Dict[str, Any]:
        """Assess if processing activity requires DPIA"""
        ...

    def generate_dpia_report(self, activity_id: str) -> Dict[str, Any]:
        """Generate complete DPIA report"""
        ...


class DPIAService:
    """Automated Data Protection Impact Assessment service"""

    def __init__(self, db: DatabaseProtocol, audit_logger: ComplianceAuditLogger):
        self.db = db
        self.audit_logger = audit_logger

        # Risk scoring criteria
        self._data_type_risk_scores = {
            "biometric_templates": 90,
            "facial_recognition_data": 90,
            "genetic_data": 95,
            "health_data": 85,
            "criminal_conviction_data": 80,
            "racial_ethnic_origin": 85,
            "religious_beliefs": 80,
            "political_opinions": 80,
            "trade_union_membership": 75,
            "sex_life_data": 90,
            "location_data": 70,
            "financial_data": 75,
            "identification_documents": 60,
            "employee_data": 50,
            "access_logs": 40,
            "contact_information": 30,
        }

        # Processing purpose risk modifiers
        self._purpose_risk_modifiers = {
            "law_enforcement": 1.3,
            "automated_decision_making": 1.4,
            "profiling": 1.3,
            "behavioral_analysis": 1.2,
            "marketing": 1.1,
            "security_monitoring": 1.2,
            "access_control": 1.0,
            "employee_management": 1.0,
            "legal_compliance": 0.9,
        }

    def assess_processing_activity(
        self,
        activity_name: str,
        data_types: List[str],
        processing_purposes: List[str],
        data_subjects_count: int,
        geographic_scope: List[str],
        automated_processing: bool = False,
        third_party_sharing: bool = False,
        retention_period_months: int = 12,
    ) -> Dict[str, Any]:
        """
        Assess if processing activity requires DPIA and calculate risk score

        Returns assessment with DPIA requirement and risk analysis
        """
        try:
            # Calculate base risk score
            base_risk_score = self._calculate_base_risk_score(data_types)

            # Apply purpose modifiers
            purpose_modifier = max(
                [
                    self._purpose_risk_modifiers.get(purpose, 1.0)
                    for purpose in processing_purposes
                ],
                default=1.0,
            )

            # Apply scale modifier
            scale_modifier = self._calculate_scale_modifier(data_subjects_count)

            # Apply technology modifier
            tech_modifier = 1.3 if automated_processing else 1.0

            # Apply sharing modifier
            sharing_modifier = 1.2 if third_party_sharing else 1.0

            # Calculate final risk score
            final_risk_score = (
                base_risk_score
                * purpose_modifier
                * scale_modifier
                * tech_modifier
                * sharing_modifier
            )

            # Determine risk level
            risk_level = self._determine_risk_level(final_risk_score)

            # Check DPIA triggers
            dpia_triggers = self._check_dpia_triggers(
                data_types,
                processing_purposes,
                data_subjects_count,
                automated_processing,
                geographic_scope,
            )

            # DPIA is required if high/critical risk or specific triggers
            dpia_required = (
                risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
                or len(dpia_triggers) > 0
            )

            assessment = {
                "activity_name": activity_name,
                "assessment_id": str(uuid4()),
                "dpia_required": dpia_required,
                "risk_level": risk_level.value,
                "risk_score": round(final_risk_score, 2),
                "risk_breakdown": {
                    "base_score": round(base_risk_score, 2),
                    "purpose_modifier": purpose_modifier,
                    "scale_modifier": scale_modifier,
                    "technology_modifier": tech_modifier,
                    "sharing_modifier": sharing_modifier,
                },
                "dpia_triggers": [trigger.value for trigger in dpia_triggers],
                "data_types_analyzed": data_types,
                "processing_purposes": processing_purposes,
                "estimated_data_subjects": data_subjects_count,
                "assessment_timestamp": datetime.now(timezone.utc).isoformat(),
                "recommendations": self._generate_recommendations(
                    risk_level, dpia_triggers
                ),
            }

            # Store assessment in database
            self._store_assessment(assessment)

            # Audit the assessment
            self.audit_logger.log_action(
                actor_user_id="system",
                action_type="DPIA_ASSESSMENT_CREATED",
                resource_type="dpia_assessment",
                resource_id=assessment["assessment_id"],
                description=f"DPIA assessment for {activity_name}: {risk_level.value} risk, DPIA {'required' if dpia_required else 'not required'}",
                legal_basis="dpia_obligation",
                data_categories=["assessment_data"],
                metadata={
                    "risk_score": final_risk_score,
                    "dpia_required": dpia_required,
                    "trigger_count": len(dpia_triggers),
                },
            )

            logger.info(
                f"DPIA assessment completed for {activity_name}: {risk_level.value} risk"
            )
            return assessment

        except Exception as e:
            logger.error(f"DPIA assessment failed: {e}")
            return {"error": str(e)}

    def generate_dpia_report(
        self,
        assessment_id: str,
        processing_description: str,
        necessity_justification: str,
        proportionality_justification: str,
        security_measures: List[str],
        consultation_stakeholders: List[str] = None,
    ) -> Dict[str, Any]:
        """Generate complete DPIA report for high-risk processing"""
        try:
            # Get assessment data
            assessment = self._get_assessment(assessment_id)
            if not assessment:
                return {"error": "Assessment not found"}

            # Generate data flow diagram data
            data_flows = self._analyze_data_flows(assessment)

            # Generate security assessment
            security_assessment = self._assess_security_measures(security_measures)

            # Generate mitigation recommendations
            mitigation_measures = self._generate_mitigation_measures(assessment)

            # Create comprehensive DPIA report
            dpia_report = {
                "dpia_id": str(uuid4()),
                "assessment_id": assessment_id,
                "report_metadata": {
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "dpia_version": "1.0",
                    "regulatory_framework": "GDPR Article 35",
                    "jurisdiction": "EU",
                },
                "processing_activity": {
                    "name": assessment["activity_name"],
                    "description": processing_description,
                    "data_types": assessment["data_types_analyzed"],
                    "purposes": assessment["processing_purposes"],
                    "legal_basis": self._determine_legal_basis(assessment),
                    "data_subjects_count": assessment["estimated_data_subjects"],
                    "retention_period": "As per retention policy",
                },
                "risk_assessment": {
                    "overall_risk_level": assessment["risk_level"],
                    "risk_score": assessment["risk_score"],
                    "identified_risks": self._identify_specific_risks(assessment),
                    "risk_to_rights_and_freedoms": self._assess_rights_impact(
                        assessment
                    ),
                    "likelihood_assessment": self._assess_likelihood(assessment),
                    "severity_assessment": self._assess_severity(assessment),
                },
                "necessity_and_proportionality": {
                    "necessity_justification": necessity_justification,
                    "proportionality_justification": proportionality_justification,
                    "alternatives_considered": self._suggest_alternatives(assessment),
                    "data_minimization_measures": self._assess_data_minimization(
                        assessment
                    ),
                },
                "security_measures": {
                    "implemented_measures": security_measures,
                    "security_assessment": security_assessment,
                    "additional_recommendations": self._recommend_security_measures(
                        assessment
                    ),
                },
                "data_flows": data_flows,
                "stakeholder_consultation": {
                    "stakeholders_consulted": consultation_stakeholders or [],
                    "consultation_summary": "Data Protection Officer consulted on assessment",
                    "consultation_date": datetime.now(timezone.utc).isoformat(),
                },
                "mitigation_measures": mitigation_measures,
                "monitoring_and_review": {
                    "review_schedule": "Annual or upon significant changes",
                    "monitoring_indicators": self._define_monitoring_indicators(
                        assessment
                    ),
                    "next_review_date": self._calculate_next_review_date(),
                },
                "conclusion": {
                    "dpia_required": assessment["dpia_required"],
                    "processing_acceptable": self._determine_processing_acceptability(
                        assessment
                    ),
                    "additional_safeguards_needed": len(mitigation_measures) > 0,
                    "dpo_opinion": "DPIA completed in accordance with GDPR Article 35",
                },
            }

            # Store DPIA report
            self._store_dpia_report(dpia_report)

            # Audit DPIA completion
            self.audit_logger.log_action(
                actor_user_id="system",
                action_type="DPIA_REPORT_GENERATED",
                resource_type="dpia_report",
                resource_id=dpia_report["dpia_id"],
                description=f"Complete DPIA report generated for {assessment['activity_name']}",
                legal_basis="dpia_obligation",
                data_categories=["dpia_report"],
                metadata={
                    "assessment_id": assessment_id,
                    "risk_level": assessment["risk_level"],
                    "processing_acceptable": dpia_report["conclusion"][
                        "processing_acceptable"
                    ],
                },
            )

            logger.info(f"DPIA report generated: {dpia_report['dpia_id']}")
            return dpia_report

        except Exception as e:
            logger.error(f"DPIA report generation failed: {e}")
            return {"error": str(e)}

    def get_dpia_dashboard_data(self) -> Dict[str, Any]:
        """Get DPIA dashboard summary for compliance monitoring"""
        try:
            # Get recent assessments
            recent_assessments_sql = """
                SELECT assessment_data 
                FROM dpia_assessments 
                WHERE created_at >= NOW() - INTERVAL '90 days'
                ORDER BY created_at DESC 
                LIMIT 20
            """

            assessments_df = execute_query(self.db, recent_assessments_sql)

            # Parse assessment data and calculate metrics
            total_assessments = len(assessments_df)
            high_risk_count = 0
            dpia_required_count = 0
            risk_distribution = {"low": 0, "medium": 0, "high": 0, "critical": 0}

            for row in assessments_df.itertuples(index=False):
                assessment_data = row.assessment_data
                if isinstance(assessment_data, str):
                    assessment_data = json.loads(assessment_data)

                risk_level = assessment_data.get("risk_level", "low")
                risk_distribution[risk_level] += 1

                if risk_level in ["high", "critical"]:
                    high_risk_count += 1

                if assessment_data.get("dpia_required", False):
                    dpia_required_count += 1

            # Get pending DPIAs
            pending_dpias_sql = """
                SELECT COUNT(*) as pending_count 
                FROM dpia_assessments 
                WHERE assessment_data->>'dpia_required' = 'true'
                  AND assessment_id NOT IN (
                      SELECT assessment_id FROM dpia_reports
                  )
            """

            pending_df = execute_query(self.db, pending_dpias_sql)
            pending_count = (
                pending_df.iloc[0]["pending_count"] if not pending_df.empty else 0
            )

            return {
                "summary": {
                    "total_assessments_90d": total_assessments,
                    "high_risk_activities": high_risk_count,
                    "dpias_required": dpia_required_count,
                    "dpias_pending": pending_count,
                    "compliance_rate": round(
                        (1 - pending_count / max(dpia_required_count, 1)) * 100, 1
                    ),
                },
                "risk_distribution": risk_distribution,
                "recent_assessments": (
                    assessments_df.to_dict("records")
                    if not assessments_df.empty
                    else []
                ),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get DPIA dashboard data: {e}")
            return {"error": str(e)}

    def _calculate_base_risk_score(self, data_types: List[str]) -> float:
        """Calculate base risk score from data types"""
        if not data_types:
            return 20.0

        max_score = max(
            [self._data_type_risk_scores.get(data_type, 30) for data_type in data_types]
        )

        # Additional risk for combining multiple sensitive data types
        if len(data_types) > 3:
            max_score *= 1.1

        return max_score

    def _calculate_scale_modifier(self, data_subjects_count: int) -> float:
        """Calculate scale modifier based on number of data subjects"""
        if data_subjects_count < 100:
            return 1.0
        elif data_subjects_count < 1000:
            return 1.1
        elif data_subjects_count < 10000:
            return 1.2
        else:
            return 1.3  # Large scale processing

    def _determine_risk_level(self, risk_score: float) -> RiskLevel:
        """Convert risk score to risk level"""
        if risk_score >= 80:
            return RiskLevel.CRITICAL
        elif risk_score >= 60:
            return RiskLevel.HIGH
        elif risk_score >= 40:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _check_dpia_triggers(
        self,
        data_types: List[str],
        purposes: List[str],
        data_subjects_count: int,
        automated_processing: bool,
        geographic_scope: List[str],
    ) -> List[DPIATrigger]:
        """Check for specific DPIA triggers per GDPR Article 35"""
        triggers = []

        # Check for biometric identification
        if any(
            dt in data_types
            for dt in ["biometric_templates", "facial_recognition_data"]
        ):
            triggers.append(DPIATrigger.BIOMETRIC_IDENTIFICATION)

        # Check for special category data
        special_categories = [
            "health_data",
            "genetic_data",
            "racial_ethnic_origin",
            "religious_beliefs",
            "political_opinions",
            "trade_union_membership",
        ]
        if any(dt in data_types for dt in special_categories):
            triggers.append(DPIATrigger.SPECIAL_CATEGORY_DATA)

        # Check for large scale processing
        if data_subjects_count >= 5000:  # Threshold for large scale
            triggers.append(DPIATrigger.LARGE_SCALE_PROCESSING)

        # Check for systematic monitoring
        if "behavioral_analysis" in purposes or "profiling" in purposes:
            triggers.append(DPIATrigger.SYSTEMATIC_MONITORING)

        # Check for automated decision making
        if automated_processing and "automated_decision_making" in purposes:
            triggers.append(DPIATrigger.AUTOMATED_DECISION_MAKING)

        # Check for public area monitoring
        if "public_area_monitoring" in purposes:
            triggers.append(DPIATrigger.PUBLIC_AREA_MONITORING)

        return triggers

    def _generate_recommendations(
        self, risk_level: RiskLevel, triggers: List[DPIATrigger]
    ) -> List[str]:
        """Generate recommendations based on risk assessment"""
        recommendations = []

        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            recommendations.append("Conduct full DPIA before processing begins")
            recommendations.append(
                "Implement additional technical and organizational measures"
            )
            recommendations.append("Consider consultation with supervisory authority")

        if DPIATrigger.BIOMETRIC_IDENTIFICATION in triggers:
            recommendations.append("Ensure explicit consent for biometric processing")
            recommendations.append(
                "Implement biometric template encryption and secure storage"
            )

        if DPIATrigger.AUTOMATED_DECISION_MAKING in triggers:
            recommendations.append(
                "Provide meaningful information about automated decision logic"
            )
            recommendations.append("Implement human review mechanisms")

        if DPIATrigger.LARGE_SCALE_PROCESSING in triggers:
            recommendations.append(
                "Appoint Data Protection Officer if not already done"
            )
            recommendations.append("Implement robust data subject rights management")

        return recommendations

    def _analyze_data_flows(self, assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze data flows for DPIA report"""
        return {
            "collection_points": [
                "Access control systems",
                "Employee onboarding",
                "Security cameras",
            ],
            "processing_locations": ["On-premises servers", "Cloud infrastructure"],
            "data_recipients": [
                "Security team",
                "HR department",
                "System administrators",
            ],
            "third_party_transfers": [],
            "retention_locations": ["Primary database", "Backup systems"],
            "deletion_process": "Automated retention policy enforcement",
        }

    def _identify_specific_risks(
        self, assessment: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Identify specific privacy risks"""
        risks = []

        data_types = assessment.get("data_types_analyzed", [])

        if "biometric_templates" in data_types:
            risks.append(
                {
                    "risk": "Biometric data breach",
                    "impact": "Permanent identity compromise - biometric data cannot be changed",
                    "likelihood": "Medium",
                    "severity": "Critical",
                }
            )

        if "behavioral_analysis" in assessment.get("processing_purposes", []):
            risks.append(
                {
                    "risk": "Discriminatory profiling",
                    "impact": "Unfair treatment based on behavioral patterns",
                    "likelihood": "Medium",
                    "severity": "High",
                }
            )

        risks.append(
            {
                "risk": "Unauthorized access",
                "impact": "Privacy violation and potential misuse of personal data",
                "likelihood": "Low",
                "severity": "High",
            }
        )

        return risks

    def _store_assessment(self, assessment: Dict[str, Any]) -> None:
        """Store DPIA assessment in database"""
        try:
            insert_sql = """
                INSERT INTO dpia_assessments 
                (assessment_id, activity_name, assessment_data, created_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (assessment_id) DO UPDATE SET
                assessment_data = EXCLUDED.assessment_data,
                updated_at = NOW()
            """

            import json

            execute_command(
                self.db,
                insert_sql,
                (
                    assessment["assessment_id"],
                    assessment["activity_name"],
                    json.dumps(assessment),
                    datetime.now(timezone.utc),
                ),
            )

        except Exception as e:
            logger.error(f"Failed to store DPIA assessment: {e}")

    def _get_assessment(self, assessment_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve DPIA assessment by ID"""
        try:
            query_sql = """
                SELECT assessment_data 
                FROM dpia_assessments 
                WHERE assessment_id = %s
            """

            df = execute_query(self.db, query_sql, (assessment_id,))
            if df.empty:
                return None

            assessment_data = df.iloc[0]["assessment_data"]
            if isinstance(assessment_data, str):
                import json

                assessment_data = json.loads(assessment_data)

            return assessment_data

        except Exception as e:
            logger.error(f"Failed to get assessment: {e}")
            return None

    # Additional helper methods for DPIA report generation
    def _determine_legal_basis(self, assessment: Dict[str, Any]) -> str:
        """Determine likely legal basis for processing"""
        purposes = assessment.get("processing_purposes", [])

        if "security_monitoring" in purposes:
            return "Legitimate interests (security of persons and property)"
        elif "employee_management" in purposes:
            return "Performance of contract (employment contract)"
        elif "legal_compliance" in purposes:
            return "Compliance with legal obligation"
        else:
            return "Consent of the data subject"

    def _assess_rights_impact(self, assessment: Dict[str, Any]) -> Dict[str, str]:
        """Assess impact on data subject rights and freedoms"""
        return {
            "privacy": "Medium impact - processing of personal data with appropriate safeguards",
            "autonomy": "Low impact - data subjects retain control through consent mechanisms",
            "discrimination": "Low risk with proper algorithm governance",
            "dignity": "Low impact with respect for person privacy",
        }

    def _assess_likelihood(self, assessment: Dict[str, Any]) -> str:
        """Assess likelihood of privacy risks materializing"""
        risk_score = assessment.get("risk_score", 0)
        if risk_score >= 70:
            return "High"
        elif risk_score >= 50:
            return "Medium"
        else:
            return "Low"

    def _assess_severity(self, assessment: Dict[str, Any]) -> str:
        """Assess severity of potential privacy impact"""
        data_types = assessment.get("data_types_analyzed", [])
        if any(dt in data_types for dt in ["biometric_templates", "health_data"]):
            return "High"
        else:
            return "Medium"


# Factory function for DI container
def create_dpia_service(
    db: DatabaseProtocol, audit_logger: ComplianceAuditLogger
) -> DPIAService:
    """Create DPIA service instance"""
    return DPIAService(db, audit_logger)


# Additional database schema for DPIA tables
DPIA_TABLES_SQL = """
-- DPIA Assessment and Report Tables

CREATE TABLE IF NOT EXISTS dpia_assessments (
    assessment_id VARCHAR(50) PRIMARY KEY,
    activity_name VARCHAR(200) NOT NULL,
    assessment_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dpia_assessments_created_at ON dpia_assessments(created_at);
CREATE INDEX IF NOT EXISTS idx_dpia_assessments_activity ON dpia_assessments(activity_name);

CREATE TABLE IF NOT EXISTS dpia_reports (
    dpia_id VARCHAR(50) PRIMARY KEY,
    assessment_id VARCHAR(50) REFERENCES dpia_assessments(assessment_id),
    report_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    approved_by VARCHAR(50),
    approval_date TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_dpia_reports_assessment_id ON dpia_reports(assessment_id);
CREATE INDEX IF NOT EXISTS idx_dpia_reports_created_at ON dpia_reports(created_at);
"""
