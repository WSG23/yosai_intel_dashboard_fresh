# services/compliance/cross_border_transfer_service.py
"""Cross-Border Data Transfer Management for GDPR Chapter V Compliance"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol
from uuid import uuid4

from yosai_intel_dashboard.src.core.audit_logger import ComplianceAuditLogger
from yosai_intel_dashboard.src.core.interfaces.protocols import DatabaseProtocol
from database.secure_exec import execute_command, execute_query

logger = logging.getLogger(__name__)


class TransferMechanism(Enum):
    """GDPR Chapter V transfer mechanisms"""

    ADEQUACY_DECISION = "adequacy_decision"  # Article 45
    STANDARD_CONTRACTUAL_CLAUSES = "scc"  # Article 46(2)(c)
    BINDING_CORPORATE_RULES = "bcr"  # Article 47
    CERTIFICATION = "certification"  # Article 46(2)(f)
    APPROVED_CODE_OF_CONDUCT = "code_of_conduct"  # Article 46(2)(e)
    DEROGATION_CONSENT = "derogation_consent"  # Article 49(1)(a)
    DEROGATION_CONTRACT = "derogation_contract"  # Article 49(1)(b)
    DEROGATION_VITAL_INTERESTS = "derogation_vital_interests"  # Article 49(1)(c)
    DEROGATION_PUBLIC_INTEREST = "derogation_public_interest"  # Article 49(1)(d)


class TransferStatus(Enum):
    """Transfer authorization status"""

    APPROVED = "approved"
    PENDING_REVIEW = "pending_review"
    REQUIRES_DOCUMENTATION = "requires_documentation"
    SUSPENDED = "suspended"
    REJECTED = "rejected"


class CrossBorderTransferServiceProtocol(Protocol):
    """Protocol for cross-border transfer operations"""

    def assess_transfer_legality(
        self, destination_country: str, data_types: List[str]
    ) -> Dict[str, Any]:
        """Assess if transfer to destination country is legal"""
        ...

    def register_transfer_activity(self, transfer_data: Dict[str, Any]) -> str:
        """Register a cross-border transfer activity"""
        ...


class CrossBorderTransferService:
    """Manages cross-border data transfers and GDPR Chapter V compliance"""

    def __init__(self, db: DatabaseProtocol, audit_logger: ComplianceAuditLogger):
        self.db = db
        self.audit_logger = audit_logger

        # EU Adequacy Decisions (as of 2025)
        self._adequacy_countries = {
            "AD",
            "AR",
            "CA",
            "FO",
            "GG",
            "IL",
            "IM",
            "JP",
            "JE",
            "NZ",
            "CH",
            "UY",
            "GB",
            "US",
        }

        # Countries with partial adequacy or special arrangements
        self._partial_adequacy = {
            "US": ["Privacy Shield successor framework", "DPF companies"],
            "GB": ["UK GDPR equivalent protection"],
            "CH": ["Swiss Federal Act on Data Protection"],
        }

        # High-risk countries requiring additional safeguards
        self._high_risk_countries = {
            "CN",
            "RU",
            "IR",
            "KP",  # Countries with concerning surveillance laws
        }

        # Standard Contractual Clauses templates
        self._scc_templates = {
            "controller_to_controller": "SCC-C2C-2021",
            "controller_to_processor": "SCC-C2P-2021",
            "processor_to_processor": "SCC-P2P-2021",
            "processor_to_controller": "SCC-P2C-2021",
        }

    def assess_transfer_legality(
        self,
        destination_country: str,
        data_types: List[str],
        transfer_purpose: str,
        data_subject_count: int,
        recipient_entity: str,
        transfer_relationship: str,  # 'controller_to_controller', etc.
    ) -> Dict[str, Any]:
        """
        Assess legality of cross-border data transfer under GDPR Chapter V

        Returns comprehensive assessment with recommended transfer mechanisms
        """
        try:
            assessment_id = f"TRANSFER-ASSESS-{str(uuid4())[:8].upper()}"

            # Check adequacy decision
            has_adequacy = destination_country.upper() in self._adequacy_countries

            # Assess data sensitivity
            sensitivity_assessment = self._assess_data_sensitivity(data_types)

            # Check for high-risk destination
            is_high_risk = destination_country.upper() in self._high_risk_countries

            # Determine required transfer mechanisms
            required_mechanisms = self._determine_transfer_mechanisms(
                destination_country,
                sensitivity_assessment,
                is_high_risk,
                transfer_relationship,
                data_subject_count,
            )

            # Assess additional safeguards needed
            additional_safeguards = self._assess_additional_safeguards(
                destination_country, data_types, sensitivity_assessment
            )

            # Generate compliance requirements
            compliance_requirements = self._generate_compliance_requirements(
                destination_country, required_mechanisms, additional_safeguards
            )

            # Determine transfer authorization status
            authorization_status = self._determine_authorization_status(
                has_adequacy, required_mechanisms, additional_safeguards, is_high_risk
            )

            assessment = {
                "assessment_id": assessment_id,
                "destination_country": destination_country,
                "has_adequacy_decision": has_adequacy,
                "is_high_risk_destination": is_high_risk,
                "data_sensitivity_level": sensitivity_assessment["overall_level"],
                "data_types_analyzed": data_types,
                "estimated_data_subjects": data_subject_count,
                "transfer_purpose": transfer_purpose,
                "recipient_entity": recipient_entity,
                "transfer_relationship": transfer_relationship,
                "required_mechanisms": [mech.value for mech in required_mechanisms],
                "additional_safeguards": additional_safeguards,
                "compliance_requirements": compliance_requirements,
                "authorization_status": authorization_status.value,
                "risk_level": self._calculate_transfer_risk_level(
                    has_adequacy,
                    sensitivity_assessment,
                    is_high_risk,
                    data_subject_count,
                ),
                "recommendations": self._generate_transfer_recommendations(
                    destination_country, required_mechanisms, additional_safeguards
                ),
                "assessment_timestamp": datetime.now(timezone.utc).isoformat(),
            }

            # Store assessment
            self._store_transfer_assessment(assessment)

            # Audit the assessment
            self.audit_logger.log_action(
                actor_user_id="system",
                action_type="CROSS_BORDER_TRANSFER_ASSESSED",
                resource_type="transfer_assessment",
                resource_id=assessment_id,
                description=f"Cross-border transfer to {destination_country} assessed: {authorization_status.value}",
                legal_basis="transfer_assessment",
                data_categories=data_types,
                metadata={
                    "destination_country": destination_country,
                    "authorization_status": authorization_status.value,
                    "has_adequacy": has_adequacy,
                    "risk_level": assessment["risk_level"],
                },
            )

            logger.info(
                f"Transfer assessment completed: {assessment_id} to {destination_country}"
            )
            return assessment

        except Exception as e:
            logger.error(f"Transfer assessment failed: {e}")
            return {"error": str(e)}

    def register_transfer_activity(
        self,
        assessment_id: str,
        transfer_mechanism: TransferMechanism,
        transfer_details: Dict[str, Any],
        authorized_by: str,
        documentation_references: List[str] = None,
    ) -> str:
        """Register an authorized cross-border transfer activity"""
        try:
            transfer_id = f"TRANSFER-{datetime.now().strftime('%Y%m%d')}-{str(uuid4())[:8].upper()}"

            # Get assessment data
            assessment = self._get_transfer_assessment(assessment_id)
            if not assessment:
                raise ValueError(f"Assessment {assessment_id} not found")

            # Validate transfer mechanism is appropriate
            if not self._validate_transfer_mechanism(assessment, transfer_mechanism):
                raise ValueError(
                    f"Transfer mechanism {transfer_mechanism.value} not appropriate for this transfer"
                )

            # Create transfer record
            transfer_record = {
                "transfer_id": transfer_id,
                "assessment_id": assessment_id,
                "destination_country": assessment["destination_country"],
                "transfer_mechanism": transfer_mechanism.value,
                "transfer_details": transfer_details,
                "authorized_by": authorized_by,
                "authorization_timestamp": datetime.now(timezone.utc),
                "documentation_references": documentation_references or [],
                "status": TransferStatus.APPROVED.value,
                "data_types": assessment["data_types_analyzed"],
                "estimated_data_subjects": assessment["estimated_data_subjects"],
                "recipient_entity": assessment["recipient_entity"],
                "transfer_purpose": assessment["transfer_purpose"],
                "compliance_monitoring": {
                    "next_review_date": self._calculate_next_review_date(
                        transfer_mechanism
                    ),
                    "monitoring_requirements": self._get_monitoring_requirements(
                        transfer_mechanism
                    ),
                    "documentation_requirements": self._get_documentation_requirements(
                        transfer_mechanism
                    ),
                },
                "created_at": datetime.now(timezone.utc),
            }

            # Store transfer record
            self._store_transfer_record(transfer_record)

            # Update assessment status
            self._update_assessment_status(assessment_id, "transfer_registered")

            # Audit the transfer registration
            self.audit_logger.log_action(
                actor_user_id=authorized_by,
                action_type="CROSS_BORDER_TRANSFER_REGISTERED",
                resource_type="data_transfer",
                resource_id=transfer_id,
                description=f"Cross-border transfer registered using {transfer_mechanism.value}",
                legal_basis="transfer_authorization",
                data_categories=assessment["data_types_analyzed"],
                metadata={
                    "destination_country": assessment["destination_country"],
                    "transfer_mechanism": transfer_mechanism.value,
                    "recipient_entity": assessment["recipient_entity"],
                },
            )

            logger.info(f"Transfer activity registered: {transfer_id}")
            return transfer_id

        except Exception as e:
            logger.error(f"Failed to register transfer activity: {e}")
            raise

    def monitor_transfer_compliance(self) -> Dict[str, Any]:
        """Monitor ongoing transfer compliance and identify issues"""
        try:
            # Get active transfers requiring review
            review_required_sql = """
                SELECT transfer_id, destination_country, transfer_mechanism, 
                       authorization_timestamp, compliance_monitoring
                FROM cross_border_transfers 
                WHERE status = 'approved'
                  AND (compliance_monitoring->>'next_review_date')::timestamp <= NOW() + INTERVAL '30 days'
                ORDER BY (compliance_monitoring->>'next_review_date')::timestamp ASC
            """

            df = execute_query(self.db, review_required_sql)
            transfers_requiring_review = df.to_dict("records") if not df.empty else []

            # Check for transfers to countries with changed adequacy status
            adequacy_changes = self._check_adequacy_status_changes()

            # Check for suspended transfers
            suspended_transfers = self._check_suspended_transfers()

            # Generate compliance report
            compliance_report = {
                "monitoring_timestamp": datetime.now(timezone.utc).isoformat(),
                "transfers_requiring_review": len(transfers_requiring_review),
                "adequacy_status_changes": adequacy_changes,
                "suspended_transfers": len(suspended_transfers),
                "compliance_issues": self._identify_compliance_issues(
                    transfers_requiring_review, adequacy_changes, suspended_transfers
                ),
                "recommended_actions": self._recommend_compliance_actions(
                    transfers_requiring_review, adequacy_changes
                ),
                "next_monitoring_date": self._calculate_next_monitoring_date(),
            }

            # Audit the monitoring activity
            self.audit_logger.log_action(
                actor_user_id="system",
                action_type="TRANSFER_COMPLIANCE_MONITORED",
                resource_type="transfer_monitoring",
                description=f"Transfer compliance monitoring completed: {len(transfers_requiring_review)} transfers need review",
                legal_basis="transfer_monitoring",
                metadata={
                    "transfers_reviewed": len(transfers_requiring_review),
                    "compliance_issues": len(compliance_report["compliance_issues"]),
                },
            )

            return compliance_report

        except Exception as e:
            logger.error(f"Transfer compliance monitoring failed: {e}")
            return {"error": str(e)}

    def get_transfer_dashboard_data(self) -> Dict[str, Any]:
        """Get cross-border transfer dashboard data"""
        try:
            # Get transfer statistics
            stats_sql = """
                SELECT 
                    destination_country,
                    transfer_mechanism,
                    COUNT(*) as transfer_count,
                    COUNT(CASE WHEN status = 'approved' THEN 1 END) as approved_count
                FROM cross_border_transfers 
                WHERE authorization_timestamp >= NOW() - INTERVAL '90 days'
                GROUP BY destination_country, transfer_mechanism
                ORDER BY transfer_count DESC
            """

            df = execute_query(self.db, stats_sql)
            transfer_stats = df.to_dict("records") if not df.empty else []

            # Get pending assessments
            pending_sql = """
                SELECT COUNT(*) as pending_count
                FROM transfer_assessments 
                WHERE assessment_data->>'authorization_status' IN ('pending_review', 'requires_documentation')
            """

            pending_df = execute_query(self.db, pending_sql)
            pending_count = (
                pending_df.iloc[0]["pending_count"] if not pending_df.empty else 0
            )

            # Calculate metrics
            total_transfers = sum(stat["transfer_count"] for stat in transfer_stats)
            adequacy_transfers = sum(
                stat["transfer_count"]
                for stat in transfer_stats
                if stat["transfer_mechanism"] == "adequacy_decision"
            )

            return {
                "summary": {
                    "total_transfers_90d": total_transfers,
                    "adequacy_decision_transfers": adequacy_transfers,
                    "pending_assessments": pending_count,
                    "adequacy_coverage_percentage": round(
                        (adequacy_transfers / max(total_transfers, 1)) * 100, 1
                    ),
                },
                "transfer_statistics": transfer_stats,
                "adequacy_countries": list(self._adequacy_countries),
                "high_risk_countries": list(self._high_risk_countries),
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            logger.error(f"Failed to get transfer dashboard data: {e}")
            return {"error": str(e)}

    def _assess_data_sensitivity(self, data_types: List[str]) -> Dict[str, Any]:
        """Assess sensitivity of data types being transferred"""
        sensitivity_scores = {
            "biometric_templates": 95,
            "health_data": 90,
            "genetic_data": 95,
            "criminal_conviction_data": 85,
            "racial_ethnic_origin": 85,
            "religious_beliefs": 80,
            "political_opinions": 80,
            "trade_union_membership": 75,
            "sex_life_data": 90,
            "children_data": 85,
            "financial_data": 75,
            "location_data": 70,
            "employee_data": 50,
            "access_logs": 40,
            "contact_information": 30,
        }

        max_score = max(
            [sensitivity_scores.get(dt, 30) for dt in data_types], default=30
        )
        avg_score = (
            sum([sensitivity_scores.get(dt, 30) for dt in data_types]) / len(data_types)
            if data_types
            else 30
        )

        if max_score >= 85:
            level = "critical"
        elif max_score >= 70:
            level = "high"
        elif max_score >= 50:
            level = "medium"
        else:
            level = "low"

        return {
            "overall_level": level,
            "max_sensitivity_score": max_score,
            "average_sensitivity_score": round(avg_score, 1),
            "data_type_scores": {
                dt: sensitivity_scores.get(dt, 30) for dt in data_types
            },
        }

    def _determine_transfer_mechanisms(
        self,
        destination_country: str,
        sensitivity_assessment: Dict[str, Any],
        is_high_risk: bool,
        transfer_relationship: str,
        data_subject_count: int,
    ) -> List[TransferMechanism]:
        """Determine appropriate transfer mechanisms"""
        mechanisms = []

        # Check adequacy decision
        if destination_country.upper() in self._adequacy_countries:
            mechanisms.append(TransferMechanism.ADEQUACY_DECISION)
        else:
            # No adequacy decision - need appropriate safeguards
            if not is_high_risk and sensitivity_assessment["overall_level"] in [
                "low",
                "medium",
            ]:
                # Standard Contractual Clauses are usually appropriate
                mechanisms.append(TransferMechanism.STANDARD_CONTRACTUAL_CLAUSES)

                # BCRs for intra-group transfers
                if "intra_group" in transfer_relationship:
                    mechanisms.append(TransferMechanism.BINDING_CORPORATE_RULES)

            elif (
                sensitivity_assessment["overall_level"] in ["high", "critical"]
                or is_high_risk
            ):
                # High-risk transfers need stronger mechanisms
                mechanisms.append(TransferMechanism.BINDING_CORPORATE_RULES)
                mechanisms.append(TransferMechanism.CERTIFICATION)

                # Derogations for specific cases
                if data_subject_count < 100:
                    mechanisms.append(TransferMechanism.DEROGATION_CONSENT)
                    mechanisms.append(TransferMechanism.DEROGATION_CONTRACT)

        return mechanisms

    def _assess_additional_safeguards(
        self,
        destination_country: str,
        data_types: List[str],
        sensitivity_assessment: Dict[str, Any],
    ) -> List[str]:
        """Assess additional safeguards needed for the transfer"""
        safeguards = []

        # Always recommend encryption in transit
        safeguards.append("encryption_in_transit")

        # Encryption at rest for sensitive data
        if sensitivity_assessment["overall_level"] in ["high", "critical"]:
            safeguards.append("encryption_at_rest")
            safeguards.append("key_management_controls")

        # Additional safeguards for high-risk countries
        if destination_country.upper() in self._high_risk_countries:
            safeguards.extend(
                [
                    "data_localization_restrictions",
                    "government_access_transparency",
                    "regular_compliance_audits",
                    "data_subject_notification_rights",
                ]
            )

        # Biometric data specific safeguards
        if any("biometric" in dt for dt in data_types):
            safeguards.extend(
                [
                    "biometric_template_protection",
                    "irreversible_anonymization_option",
                    "purpose_limitation_enforcement",
                ]
            )

        return list(set(safeguards))  # Remove duplicates

    def _generate_compliance_requirements(
        self,
        destination_country: str,
        mechanisms: List[TransferMechanism],
        safeguards: List[str],
    ) -> Dict[str, Any]:
        """Generate specific compliance requirements"""
        requirements = {
            "documentation_required": [],
            "contractual_requirements": [],
            "technical_requirements": safeguards,
            "monitoring_requirements": [],
            "notification_requirements": [],
        }

        for mechanism in mechanisms:
            if mechanism == TransferMechanism.STANDARD_CONTRACTUAL_CLAUSES:
                requirements["documentation_required"].extend(
                    [
                        "signed_scc_agreement",
                        "transfer_impact_assessment",
                        "supplementary_measures_documentation",
                    ]
                )
                requirements["contractual_requirements"].extend(
                    [
                        "scc_module_implementation",
                        "data_subject_rights_provisions",
                        "audit_rights_clauses",
                    ]
                )

            elif mechanism == TransferMechanism.BINDING_CORPORATE_RULES:
                requirements["documentation_required"].extend(
                    ["approved_bcr_documentation", "bcr_compliance_monitoring_reports"]
                )
                requirements["monitoring_requirements"].extend(
                    ["annual_bcr_compliance_review", "data_subject_complaint_handling"]
                )

        return requirements

    def _store_transfer_assessment(self, assessment: Dict[str, Any]) -> None:
        """Store transfer assessment in database"""
        try:
            insert_sql = """
                INSERT INTO transfer_assessments 
                (assessment_id, destination_country, assessment_data, created_at)
                VALUES (%s, %s, %s, %s)
            """

            import json

            execute_command(
                self.db,
                insert_sql,
                (
                    assessment["assessment_id"],
                    assessment["destination_country"],
                    json.dumps(assessment),
                    datetime.now(timezone.utc),
                ),
            )

        except Exception as e:
            logger.error(f"Failed to store transfer assessment: {e}")


# Factory function for DI container
def create_cross_border_transfer_service(
    db: DatabaseProtocol, audit_logger: ComplianceAuditLogger
) -> CrossBorderTransferService:
    """Create cross-border transfer service instance"""
    return CrossBorderTransferService(db, audit_logger)


# Database schema for cross-border transfer tables
CROSS_BORDER_TRANSFER_TABLES_SQL = """
-- Cross-Border Transfer Management Tables

CREATE TABLE IF NOT EXISTS transfer_assessments (
    assessment_id VARCHAR(50) PRIMARY KEY,
    destination_country VARCHAR(5) NOT NULL,
    assessment_data JSONB NOT NULL,
    status VARCHAR(30) DEFAULT 'completed',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transfer_assessments_country ON transfer_assessments(destination_country);
CREATE INDEX IF NOT EXISTS idx_transfer_assessments_created_at ON transfer_assessments(created_at);

CREATE TABLE IF NOT EXISTS cross_border_transfers (
    transfer_id VARCHAR(50) PRIMARY KEY,
    assessment_id VARCHAR(50) REFERENCES transfer_assessments(assessment_id),
    destination_country VARCHAR(5) NOT NULL,
    transfer_mechanism VARCHAR(50) NOT NULL,
    transfer_details JSONB,
    authorized_by VARCHAR(50) NOT NULL,
    authorization_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    documentation_references JSONB,
    status VARCHAR(30) NOT NULL DEFAULT 'approved',
    data_types JSONB,
    estimated_data_subjects INTEGER,
    recipient_entity VARCHAR(200),
    transfer_purpose VARCHAR(200),
    compliance_monitoring JSONB,
    suspension_reason TEXT,
    suspension_timestamp TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_cross_border_transfers_country ON cross_border_transfers(destination_country);
CREATE INDEX IF NOT EXISTS idx_cross_border_transfers_mechanism ON cross_border_transfers(transfer_mechanism);
CREATE INDEX IF NOT EXISTS idx_cross_border_transfers_status ON cross_border_transfers(status);
CREATE INDEX IF NOT EXISTS idx_cross_border_transfers_auth_timestamp ON cross_border_transfers(authorization_timestamp);

CREATE TABLE IF NOT EXISTS transfer_compliance_reviews (
    review_id VARCHAR(50) PRIMARY KEY,
    transfer_id VARCHAR(50) REFERENCES cross_border_transfers(transfer_id),
    review_date TIMESTAMP WITH TIME ZONE NOT NULL,
    reviewer VARCHAR(50) NOT NULL,
    compliance_status VARCHAR(30) NOT NULL,
    findings TEXT,
    recommendations TEXT,
    next_review_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_transfer_compliance_reviews_transfer_id ON transfer_compliance_reviews(transfer_id);
CREATE INDEX IF NOT EXISTS idx_transfer_compliance_reviews_review_date ON transfer_compliance_reviews(review_date);
"""
