# TimescaleDB Integration

The dashboard can store access events in TimescaleDB for efficient time-series
analytics. Hypertables are created automatically when the `TimescaleDBManager`
initialises. By default the hypertables are partitioned into daily chunks, but
the interval can be adjusted (e.g. to `1 month`) using the
`TIMESCALE_CHUNK_INTERVAL` environment variable. Events are compressed after
thirty days and removed after one year using retention policies. The policy
durations can be overridden with the environment variables
`TIMESCALE_COMPRESSION_DAYS` and `TIMESCALE_RETENTION_DAYS`.


## Data Retention

```sql
SELECT add_compression_policy('access_events', INTERVAL '30 days');
SELECT add_retention_policy('access_events', INTERVAL '365 days');
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

## Replication CronJob

Add the `timescale-replication` CronJob to periodically copy new events from the
primary database. The job simply executes `scripts/replicate_to_timescale.py`
inside the standard dashboard image. Connection strings are fetched from Vault
using the `secret/data/timescale` path.

Example schedule running every five minutes:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: timescale-replication
spec:
  schedule: "*/5 * * * *"
  jobTemplate:
    spec:
      template:
        spec:
          securityContext:
            runAsUser: 1000
            runAsGroup: 1000
            fsGroup: 1000
          restartPolicy: OnFailure
          containers:
            - name: replicate-to-timescale
              image: yosai-intel-dashboard:${IMAGE_TAG:-v0.1.0}
              imagePullPolicy: IfNotPresent
              command: ["python", "scripts/replicate_to_timescale.py"]
```

The job also inherits the standard configuration from `yosai-config` and `yosai-secrets` via `envFrom` like the other microservices.

## Backup and Restore

Use `scripts/backup_timescale.sh` to create pg_dump archives of the Timescale database. Set `TIMESCALE_DSN` to the connection string and optionally `OUTPUT_DIR` and `RETENTION_DAYS`.

```bash
TIMESCALE_DSN=postgres://user:pass@db/timescale ./scripts/backup_timescale.sh
```

The script verifies the dump with `pg_restore --list` and removes backups older than `RETENTION_DAYS` (default 7 days).

Restore a dump with `scripts/restore_timescale.sh`:

```bash
TIMESCALE_DSN=postgres://user:pass@db/timescale ./scripts/restore_timescale.sh backups/timescale_20240101_120000.dump
```

Always check that the restore completed successfully and that the expected tables are present.

