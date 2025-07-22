# Service Restart Runbook

This guide covers how to safely restart dashboard services.

## Overview
A restart may be required after configuration changes or when a service becomes unresponsive.

## Fetching Logs
Before restarting, capture the current logs:

```bash
sudo journalctl -u dashboard.service --since "10 minutes ago" > /tmp/dashboard.log
```

Attach this file to any incident ticket for reference.

## Contacting On-Call Engineers
If you are unsure whether a restart is safe, contact the on-call engineer via Slack `#ops-oncall` or phone `+1-555-0100`.

## Resolution Steps
1. SSH into the affected server.
2. Run `sudo systemctl restart dashboard.service`.
3. Verify the status with `sudo systemctl status dashboard.service`.
4. Check the logs again to confirm the service started correctly:
   ```bash
   sudo journalctl -u dashboard.service -n 50
   ```
5. If issues persist, escalate to the on-call engineer.
