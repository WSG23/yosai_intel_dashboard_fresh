# Runbooks

This directory contains standard operating procedures for the Yosai Intel Dashboard.

## Routine Operations

- **Restart services** using `docker-compose restart <service>` or `kubectl rollout restart deployment/<service>`.
- **Check health** endpoints at `/v1/health` and review Prometheus targets for scrape status.
- **View metrics** in Grafana dashboards under the `gateway`, `event-processor` and `database` folders.
- **Validate logs** in staging by searching for recent correlation IDs in Kibana and the Datadog Log Explorer.

## Incident Response

1. Confirm alerts in Prometheus and review related Grafana panels.
2. Inspect recent spans in Jaeger to pinpoint failing components.
3. If the issue cannot be mitigated within 30 minutes, escalate using the chain below.

### Escalation Path

1. Primary on-call engineer – `oncall@example.com`
2. Team lead – `teamlead@example.com`
3. Director of operations – `director@example.com`
