# Restore Dry-Run

This runbook documents a dry-run procedure for restoring a TimescaleDB backup. Use it to verify that backups created by `deploy/db/backup/backup.sh` can be restored successfully.

## Prerequisites
- A recent backup created by the backup job.
- Access to a disposable TimescaleDB instance for validation.

## Steps
1. Load the backup configuration and set the database connection:
   ```bash
   source deploy/db/backup/backup.conf
   export TIMESCALE_DSN="postgres://user:pass@localhost:5432/postgres"
   ```
2. List the contents of the backup to ensure it is valid:
   ```bash
   pg_restore --list "$OUTPUT_DIR/$(ls -t "$OUTPUT_DIR" | head -n1)"
   ```
3. Perform a restore into the test database:
   ```bash
   scripts/restore_timescale.sh "$OUTPUT_DIR/$(ls -t "$OUTPUT_DIR" | head -n1)"
   ```
4. Inspect the logs for errors. If none are found, the dry-run is successful.
5. Tear down the test database instance.

## Notes
- The production database is untouched during this procedure.
- Remove any temporary resources created for the dry-run once verification is complete.
