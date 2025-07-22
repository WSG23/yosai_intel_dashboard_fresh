# Cache Flush Runbook

Use this guide when cached data becomes stale or when troubleshooting inconsistent results.

## Overview
Flushing the cache clears temporary data stored in Redis and forces the service to rebuild it.

## Fetching Logs
Review the cache logs before and after flushing:

```bash
sudo journalctl -u redis.service --since "10 minutes ago" > /tmp/redis.log
```

Include this log in the incident ticket.

## Contacting On-Call Engineers
Reach the on-call engineer through Slack `#ops-oncall` or phone `+1-555-0100` if the flush does not resolve the issue.

## Resolution Steps
1. SSH into the server hosting Redis.
2. Connect to Redis:
   ```bash
   redis-cli
   ```
3. Flush the cache:
   ```
   FLUSHALL
   ```
4. Exit Redis and monitor the application logs to verify normal operation.
5. If performance degrades or errors appear, escalate to the on-call engineer.
