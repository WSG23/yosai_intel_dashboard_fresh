CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Main access event table using TimescaleDB
CREATE TABLE IF NOT EXISTS access_events (
    time TIMESTAMPTZ NOT NULL,
    event_id UUID PRIMARY KEY,
    person_id VARCHAR(50),
    door_id VARCHAR(50),
    facility_id VARCHAR(50),
    access_result VARCHAR(20),
    badge_status VARCHAR(20),
    response_time_ms INTEGER,
    metadata JSONB
);

SELECT create_hypertable('access_events', 'time', if_not_exists => TRUE);
ALTER TABLE access_events
  SET (
       timescaledb.compress,
       timescaledb.compress_orderby = 'time DESC',
       timescaledb.compress_segmentby = 'facility_id'
  );

-- Common indexes for query patterns
CREATE INDEX IF NOT EXISTS idx_access_events_time ON access_events(time);
CREATE INDEX IF NOT EXISTS idx_access_events_person_id ON access_events(person_id);
CREATE INDEX IF NOT EXISTS idx_access_events_door_id ON access_events(door_id);
CREATE INDEX IF NOT EXISTS idx_access_events_facility_id ON access_events(facility_id);

-- Continuous aggregate for fast summaries
CREATE MATERIALIZED VIEW IF NOT EXISTS access_events_5min
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('5 minutes', time) AS bucket,
    facility_id,
    COUNT(*) AS event_count
FROM access_events
GROUP BY bucket, facility_id
WITH NO DATA;

SELECT add_continuous_aggregate_policy('access_events_5min',
    start_offset => INTERVAL '1 day',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '5 minutes');

SELECT add_compression_policy('access_events', INTERVAL '30 days');
SELECT add_retention_policy('access_events', INTERVAL '365 days');

-- Authorization related tables
CREATE TABLE IF NOT EXISTS door_groups (
    group_id SERIAL PRIMARY KEY,
    group_name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS person_roles (
    person_id VARCHAR(50) NOT NULL,
    role VARCHAR(50) NOT NULL,
    PRIMARY KEY (person_id, role)
);

CREATE TABLE IF NOT EXISTS access_permissions (
    permission_id SERIAL PRIMARY KEY,
    person_id VARCHAR(50) NOT NULL,
    door_id VARCHAR(50) NOT NULL,
    valid_from TIMESTAMPTZ,
    valid_to TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_access_permissions_person_id ON access_permissions(person_id);
CREATE INDEX IF NOT EXISTS idx_access_permissions_door_id ON access_permissions(door_id);

CREATE TABLE IF NOT EXISTS access_blocklist (
    person_id VARCHAR(50) PRIMARY KEY,
    reason TEXT,
    blocked_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS time_restrictions (
    restriction_id SERIAL PRIMARY KEY,
    door_id VARCHAR(50),
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    days_of_week INT[]
);
CREATE INDEX IF NOT EXISTS idx_time_restrictions_door_id ON time_restrictions(door_id);

CREATE TABLE IF NOT EXISTS anti_passback_state (
    person_id VARCHAR(50) PRIMARY KEY,
    last_direction VARCHAR(10),
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS emergency_lockdowns (
    facility_id VARCHAR(50) PRIMARY KEY,
    active BOOLEAN DEFAULT FALSE,
    activated_at TIMESTAMPTZ
);

-- Anomaly detections stored as a hypertable for efficient retention and compression
CREATE TABLE IF NOT EXISTS anomaly_detections (
    anomaly_id UUID PRIMARY KEY,
    event_id UUID REFERENCES access_events(event_id),
    anomaly_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    confidence_score FLOAT NOT NULL,
    description TEXT,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ai_model_version VARCHAR(50),
    additional_context JSONB,
    is_verified BOOLEAN,
    verified_by VARCHAR(50),
    verified_at TIMESTAMPTZ
);
SELECT create_hypertable('anomaly_detections', 'detected_at', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_anomaly_detections_detected_at ON anomaly_detections(detected_at);
CREATE INDEX IF NOT EXISTS idx_anomaly_detections_type ON anomaly_detections(anomaly_type);
ALTER TABLE anomaly_detections
  SET (
       timescaledb.compress,
       timescaledb.compress_orderby = 'detected_at DESC'
  );
SELECT add_compression_policy('anomaly_detections', INTERVAL '30 days');
SELECT add_retention_policy('anomaly_detections', INTERVAL '180 days');
