# Database Failover Runbook

Follow this procedure when the primary PostgreSQL instance becomes unavailable.

## Overview
High availability is provided through streaming replication. A failover promotes the standby server to primary.

## Fetching Logs
Collect the latest database logs from both servers:

```bash
sudo journalctl -u postgres.service --since "10 minutes ago" > /tmp/postgres.log
```

Include these logs with the incident details.

## Contacting On-Call Engineers
Immediately page the on-call database engineer through Slack `#db-oncall` or phone `+1-555-0101`.

## Resolution Steps
1. Confirm that the primary is down and the standby is healthy.
2. Promote the standby:
   ```bash
   sudo -u postgres pg_ctlcluster 14 main promote
   ```
3. Update any load balancers or application configs to point at the new primary.
4. Monitor replication status once the old primary comes back online.
5. Plan a switchover back to the original primary during the next maintenance window.

## Database Migrations
Use the migration CLI to manage schema changes:

```bash
python scripts/db_migration_cli.py upgrade      # apply latest migrations
python scripts/db_migration_cli.py downgrade <rev>
python scripts/db_migration_cli.py rollback
```
