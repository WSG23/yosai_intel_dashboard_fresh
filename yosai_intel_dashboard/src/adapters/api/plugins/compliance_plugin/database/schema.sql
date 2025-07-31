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
    additional_metadata JSONB
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
