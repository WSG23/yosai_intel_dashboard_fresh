# Data Archival

## Scheduling

Use `scripts/archive_cold_data.py` to move cold data to object storage. Schedule
the job via cron:

```
0 1 * * * /usr/bin/python3 /app/scripts/archive_cold_data.py
```

This runs the archival daily at 1 AM and removes local files once they are
safely stored in the S3 bucket.

## Retention and Retrieval

Retention settings live in `config/data_archival.yaml`. Files older than the
configured `retention_days` are archived. Archived data can be retrieved by
copying it back from the object store:

```
aws s3 cp s3://intel-cold-data/<object-key> /var/lib/app/restored/
```

Items restored to the local `restore_directory` should be cleaned up after
`default_expiry_days` to avoid unnecessary storage.

## Monitoring

Archival monitoring thresholds reside in `config/monitoring.yaml`. The archival
script logs each archived file along with the total storage size and estimated
monthly cost. Pipe these logs to your metrics system to alert on low success
rates or rising storage costs.
