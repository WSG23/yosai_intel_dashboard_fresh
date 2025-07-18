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
SELECT create_hypertable('access_events', 'time', if_not_exists => TRUE);
ALTER TABLE access_events
  SET (timescaledb.compress,
       timescaledb.compress_orderby = 'time DESC',
       timescaledb.compress_segmentby = 'facility_id');
SELECT add_compression_policy('access_events', INTERVAL '1 day');
SELECT add_retention_policy('access_events', INTERVAL '7 days');
