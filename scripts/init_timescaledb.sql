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
ALTER TABLE access_events
  SET (timescaledb.compress,
       timescaledb.compress_orderby = 'time DESC',
       timescaledb.compress_segmentby = 'facility_id');
-- Indexes for common query patterns
CREATE INDEX IF NOT EXISTS idx_access_events_time ON access_events(time);
CREATE INDEX IF NOT EXISTS idx_access_events_person_id ON access_events(person_id);
CREATE INDEX IF NOT EXISTS idx_access_events_door_id ON access_events(door_id);
CREATE INDEX IF NOT EXISTS idx_access_events_facility_id ON access_events(facility_id);

-- Continuous aggregate for quick 5 minute summaries
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
