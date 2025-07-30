# models/compliance.py
"""GDPR/APPI Compliance Database Models"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class DataSensitivityLevel(Enum):
    """Data sensitivity classification"""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SPECIAL_CATEGORY = "special_category"  # GDPR Article 9 / APPI special care-required


class ConsentType(Enum):
    """Types of consent for data processing"""

    BIOMETRIC_ACCESS = "biometric_access"
    SECURITY_ANALYTICS = "security_analytics"
    FACIAL_RECOGNITION = "facial_recognition"
    LOCATION_TRACKING = "location_tracking"
    BEHAVIORAL_ANALYSIS = "behavioral_analysis"


class DSARRequestType(Enum):
    """Data Subject Access Request types"""

    ACCESS = "access"  # Right to access
    PORTABILITY = "portability"  # Right to data portability
    RECTIFICATION = "rectification"  # Right to rectification
    ERASURE = "erasure"  # Right to erasure/"be forgotten"
    RESTRICTION = "restriction"  # Right to restrict processing


class DSARStatus(Enum):
    """DSAR request status"""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"


class ConsentLog(Base):
    """Immutable consent tracking table"""

    __tablename__ = "consent_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(String(50), nullable=False, index=True)
    consent_type = Column(SQLEnum(ConsentType), nullable=False)
    jurisdiction = Column(String(5), nullable=False)  # 'EU', 'JP', 'US', etc.
    is_active = Column(Boolean, nullable=False, default=True)
    granted_timestamp = Column(
        DateTime(timezone=True), nullable=False, default=func.now()
    )
    withdrawn_timestamp = Column(DateTime(timezone=True), nullable=True)
    policy_version = Column(String(20), nullable=False)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    legal_basis = Column(
        String(50), nullable=False, default="consent"
    )  # GDPR Article 6
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())

    # Ensure uniqueness per user/consent type/jurisdiction
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "consent_type",
            "jurisdiction",
            "is_active",
            name="_user_consent_jurisdiction_active_uc",
        ),
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "user_id": self.user_id,
            "consent_type": self.consent_type.value,
            "jurisdiction": self.jurisdiction,
            "is_active": self.is_active,
            "granted_timestamp": self.granted_timestamp.isoformat(),
            "withdrawn_timestamp": (
                self.withdrawn_timestamp.isoformat()
                if self.withdrawn_timestamp
                else None
            ),
            "policy_version": self.policy_version,
            "legal_basis": self.legal_basis,
            "created_at": self.created_at.isoformat(),
        }


class DSARRequest(Base):
    """Data Subject Access Request tracking"""

    __tablename__ = "dsar_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    request_id = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    request_type = Column(SQLEnum(DSARRequestType), nullable=False)
    status = Column(SQLEnum(DSARStatus), nullable=False, default=DSARStatus.PENDING)
    jurisdiction = Column(String(5), nullable=False)
    received_date = Column(DateTime(timezone=True), nullable=False, default=func.now())
    due_date = Column(
        DateTime(timezone=True), nullable=False
    )  # 30 days GDPR, varies by jurisdiction
    fulfilled_date = Column(DateTime(timezone=True), nullable=True)
    requestor_email = Column(String(255), nullable=False)
    request_details = Column(JSONB, nullable=True)  # Additional request context
    response_data = Column(JSONB, nullable=True)  # Response payload for access requests
    processed_by = Column(String(50), nullable=True)  # Staff member who processed
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now()
    )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "request_id": self.request_id,
            "user_id": self.user_id,
            "request_type": self.request_type.value,
            "status": self.status.value,
            "jurisdiction": self.jurisdiction,
            "received_date": self.received_date.isoformat(),
            "due_date": self.due_date.isoformat(),
            "fulfilled_date": (
                self.fulfilled_date.isoformat() if self.fulfilled_date else None
            ),
            "requestor_email": self.requestor_email,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class ComplianceAuditLog(Base):
    """Immutable audit log for all personal data operations"""

    __tablename__ = "compliance_audit_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    timestamp = Column(
        DateTime(timezone=True), nullable=False, default=func.now(), index=True
    )
    actor_user_id = Column(
        String(50), nullable=False, index=True
    )  # Who performed the action
    target_user_id = Column(
        String(50), nullable=True, index=True
    )  # Whose data was affected
    action_type = Column(
        String(100), nullable=False, index=True
    )  # VIEW_PROFILE, DELETE_BIOMETRIC_DATA, etc.
    resource_type = Column(
        String(50), nullable=False
    )  # 'user_profile', 'biometric_data', etc.
    resource_id = Column(String(100), nullable=True)  # Specific resource identifier
    source_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True)  # Trace requests across services
    description = Column(Text, nullable=False)
    legal_basis = Column(String(50), nullable=True)  # Which legal basis was used
    data_categories = Column(JSONB, nullable=True)  # What types of data were involved
    additional_metadata = Column(JSONB, nullable=True)  # Additional context

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": str(self.id),
            "timestamp": self.timestamp.isoformat(),
            "actor_user_id": self.actor_user_id,
            "target_user_id": self.target_user_id,
            "action_type": self.action_type,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "source_ip": self.source_ip,
            "description": self.description,
            "legal_basis": self.legal_basis,
            "data_categories": self.data_categories,
            "additional_metadata": self.additional_metadata,
        }


class DataRetentionPolicy(Base):
    """Data retention policies per data type"""

    __tablename__ = "data_retention_policies"

    id = Column(Integer, primary_key=True)
    data_type = Column(
        String(100), unique=True, nullable=False
    )  # 'biometric_templates', 'access_logs', etc.
    retention_days = Column(Integer, nullable=False)
    legal_basis = Column(String(50), nullable=False)
    jurisdiction = Column(String(5), nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(
        DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now()
    )


# SQL for creating tables (for database_setup.sql)
CREATE_COMPLIANCE_TABLES_SQL = """
-- GDPR/APPI Compliance Tables

CREATE TABLE IF NOT EXISTS consent_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(50) NOT NULL,
    consent_type VARCHAR(50) NOT NULL,
    jurisdiction VARCHAR(5) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    granted_timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    withdrawn_timestamp TIMESTAMP WITH TIME ZONE,
    policy_version VARCHAR(20) NOT NULL,
    ip_address VARCHAR(45),
    user_agent TEXT,
    legal_basis VARCHAR(50) NOT NULL DEFAULT 'consent',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    CONSTRAINT _user_consent_jurisdiction_active_uc 
        UNIQUE (user_id, consent_type, jurisdiction, is_active)
);

CREATE INDEX IF NOT EXISTS idx_consent_log_user_id ON consent_log(user_id);
CREATE INDEX IF NOT EXISTS idx_consent_log_consent_type ON consent_log(consent_type);

CREATE TABLE IF NOT EXISTS dsar_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id VARCHAR(50) UNIQUE NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    request_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    jurisdiction VARCHAR(5) NOT NULL,
    received_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    due_date TIMESTAMP WITH TIME ZONE NOT NULL,
    fulfilled_date TIMESTAMP WITH TIME ZONE,
    requestor_email VARCHAR(255) NOT NULL,
    request_details JSONB,
    response_data JSONB,
    processed_by VARCHAR(50),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_dsar_requests_user_id ON dsar_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_dsar_requests_status ON dsar_requests(status);
CREATE INDEX IF NOT EXISTS idx_dsar_requests_due_date ON dsar_requests(due_date);

CREATE TABLE IF NOT EXISTS compliance_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    actor_user_id VARCHAR(50) NOT NULL,
    target_user_id VARCHAR(50),
    action_type VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    resource_id VARCHAR(100),
    source_ip VARCHAR(45),
    user_agent TEXT,
    request_id VARCHAR(100),
    description TEXT NOT NULL,
    legal_basis VARCHAR(50),
    data_categories JSONB,
    metadata JSONB
);

CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON compliance_audit_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_audit_log_actor ON compliance_audit_log(actor_user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_target ON compliance_audit_log(target_user_id);
CREATE INDEX IF NOT EXISTS idx_audit_log_action_type ON compliance_audit_log(action_type);

CREATE TABLE IF NOT EXISTS data_retention_policies (
    id SERIAL PRIMARY KEY,
    data_type VARCHAR(100) UNIQUE NOT NULL,
    retention_days INTEGER NOT NULL,
    legal_basis VARCHAR(50) NOT NULL,
    jurisdiction VARCHAR(5) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Add data sensitivity column to existing people table
ALTER TABLE people ADD COLUMN IF NOT EXISTS data_sensitivity_level VARCHAR(20) DEFAULT 'internal';
ALTER TABLE people ADD COLUMN IF NOT EXISTS consent_status JSONB DEFAULT '{}';
ALTER TABLE people ADD COLUMN IF NOT EXISTS data_retention_date TIMESTAMP WITH TIME ZONE;

-- Add data sensitivity to access_events table 
ALTER TABLE access_events ADD COLUMN IF NOT EXISTS contains_biometric_data BOOLEAN DEFAULT FALSE;
ALTER TABLE access_events ADD COLUMN IF NOT EXISTS data_sensitivity_level VARCHAR(20) DEFAULT 'confidential';
"""
