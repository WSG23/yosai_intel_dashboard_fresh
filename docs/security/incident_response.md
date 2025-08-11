# Security Incident Response

This runbook outlines the actions to take when a security alert fires.

## Alert Triage

1. **Confirm the alert**
   - Check monitoring dashboards for correlated anomalies.
   - Verify the rule and severity.
2. **Gather context**
   - Identify affected services, regions, and user impact.
   - Record the alert ID, timestamp, and triggering rule.
3. **Assign roles and escalate**
   - Page the on-call security engineer.
   - Nominate an incident commander to coordinate the response.
4. **Contain**
   - Isolate compromised hosts or revoke exposed credentials.
   - Document all actions in the incident tracker.

## Log Locations

| Source | Location or command |
| ------ | ------------------- |
| Application logs | `kubectl logs <pod>` or `/var/log/yosai/app.log` |
| Gateway logs | `kubectl logs -l app=gateway` |
| Database logs | `/var/log/postgresql/postgresql.log` |
| Network flow logs | `logging/promtail-config.yml` or monitoring dashboards |
| Audit trail | `vault/audit.log` |

## Forensic Data Collection

- Snapshot affected containers: `docker commit <container> ir-<id>`.
- Export system metrics: `kubectl top pod <pod>` and node stats.
- Capture memory dumps if compromise is suspected.
- Preserve configuration files and environment variables.
- Hash all artifacts and store them in a secure evidence bucket.

## Rollback Procedures

1. Follow the [Kubernetes Rollback Procedure](../rollback.md).
2. Run `./scripts/rollback.sh <service> <namespace>` to switch traffic.
3. Redeploy known-good images from the registry.
4. Validate recovery with health checks and smoke tests.
5. Note the rollback in the post-incident report.

## Communication Templates

**Internal Notification**

```
Subject: [SEV{X}] Security Incident - {Summary}

A security alert triggered at {time}. Impacted service: {service}.

Current status: {triage/containment progress}.
Next update in {interval}.

- Incident Commander
```

**External Stakeholder Update**

```
Subject: Notice of Security Incident

We detected suspicious activity affecting {service} on {date}.
We have contained the issue and are investigating.

User impact: {impact}
Next steps: {remediation actions}

We will provide updates as more information becomes available.
```

