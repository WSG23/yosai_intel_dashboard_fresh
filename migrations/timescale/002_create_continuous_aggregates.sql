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
