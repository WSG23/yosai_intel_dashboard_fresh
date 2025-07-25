ALTER TABLE access_events
  SET (
       timescaledb.compress,
       timescaledb.compress_orderby = 'time DESC',
       timescaledb.compress_segmentby = 'facility_id'
  );

SELECT add_compression_policy('access_events', INTERVAL '30 days');
