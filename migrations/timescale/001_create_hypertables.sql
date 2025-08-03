CREATE EXTENSION IF NOT EXISTS timescaledb;

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
SELECT create_hypertable('access_events', 'time', chunk_time_interval => INTERVAL '1 day', if_not_exists => TRUE);

-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_access_events_time ON access_events(time);
CREATE INDEX IF NOT EXISTS idx_access_events_person_id ON access_events(person_id);
CREATE INDEX IF NOT EXISTS idx_access_events_door_id ON access_events(door_id);
CREATE INDEX IF NOT EXISTS idx_access_events_facility_id ON access_events(facility_id);

-- Anomaly detections hypertable
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
