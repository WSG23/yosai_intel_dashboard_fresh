# TimescaleDB Integration

The dashboard can store access events in TimescaleDB for efficient time-series
analytics. Hypertables are created automatically when the `TimescaleDBManager`
initialises. Events are compressed after seven days and removed after ninety
days using retention policies.

## Data Retention

```sql
SELECT add_compression_policy('access_events', INTERVAL '7 days');
SELECT add_retention_policy('access_events', INTERVAL '90 days');
```

Continuous aggregates refresh every five minutes to keep summary data up to
date. Use the following query to inspect the hypertable size:

```sql
SELECT hypertable_schema, hypertable_name, total_bytes
FROM timescaledb_information.hypertables_size
ORDER BY total_bytes DESC;
```

## Monitoring Queries

Replication lag from PostgreSQL can be checked with:

```sql
SELECT NOW() - max(time) AS lag
FROM access_events;
```

Expose the lag via Prometheus by exporting a gauge named
`replication_lag_seconds` in the replication job. The hypertable size can be
exported with a gauge `hypertable_bytes_total`.
