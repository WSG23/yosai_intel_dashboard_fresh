# Deprecation Timeline

This file is auto-generated from `deprecation.yml`.

| Component | Deprecated Since | Removal Version |
|-----------|-----------------|-----------------|
| legacy-auth | 1.2.0 | 2.0.0 |
| old-dashboard | 1.5.0 | 2.1.0 |

## Migration Guides

Migration instructions for deprecated components will appear here.

## Impact Analysis

This section will detail user impact and remediation steps.

## Monitoring

Deprecated component usage is tracked via the `deprecation_usage_total` Prometheus metric.
The Grafana dashboard lives in `dashboards/grafana/deprecation-usage.json` and alert rules
are defined in `monitoring/prometheus/rules/deprecation_alerts.yml`.
