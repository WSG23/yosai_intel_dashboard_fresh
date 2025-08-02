# Deprecation Timeline

This document summarizes features scheduled for removal and links to their migration guides. All data is sourced from `deprecation.yml`.

## Summary

| Component | Deprecated Since | Removal Version | Migration Guide |
|-----------|-----------------|-----------------|----------------|
| legacy-auth | 1.2.0 | 2.0.0 | [Legacy Auth Migration](migration/legacy-auth.md) |
| old-dashboard | 1.5.0 | 2.1.0 | [New Dashboard Migration](migration/new-dashboard.md) |

- [Legacy Auth Migration](migration/legacy-auth.md)
- [New Dashboard Migration](migration/new-dashboard.md)


This section will detail user impact and remediation steps.

## Monitoring

Deprecated component usage is tracked via the `deprecation_usage_total` Prometheus metric.
The Grafana dashboard lives in `dashboards/grafana/deprecation-usage.json` and alert rules
are defined in `monitoring/prometheus/rules/deprecation_alerts.yml`.
