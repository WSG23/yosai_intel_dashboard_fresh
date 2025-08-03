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

CREATE MATERIALIZED VIEW IF NOT EXISTS access_event_hourly
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', time) AS bucket,
    facility_id,
    COUNT(*) AS event_count
FROM access_events
GROUP BY bucket, facility_id
WITH NO DATA;

SELECT add_continuous_aggregate_policy('access_event_hourly',
    start_offset => INTERVAL '7 days',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');
