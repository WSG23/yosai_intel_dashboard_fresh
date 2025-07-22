# Operations Guide

This document outlines how to monitor the dashboard and configure alerts.

## Alert Configuration

Alerts are emitted when background tasks fail or exceed the configured
threshold. Set the notification email and severity level in your YAML
configuration:

```yaml
alerts:
  email: ops@example.com
  severity_threshold: warning
```

The application sends messages to this address using the SMTP settings defined in
`config`. You can override these values via environment variables in production.

## Performance Dashboards

Prometheus scrapes metrics from `/metrics` using the sample
`monitoring/prometheus.yml`. Import this data source into Grafana to build CPU,
memory and request charts. Logs can be forwarded to Elasticsearch through
`logging/logstash.conf` and visualized with Kibana.

## Canary Deployments

Production releases use a short canary phase before rolling out fully. The CI/CD pipeline first applies manifests from `k8s/canary` which deploy a single replica alongside the existing deployment. Kubernetes waits for the canary pod to become ready.

You can verify the canary status with:

```bash
kubectl get pods -l track=canary
```

If the canary remains healthy the workflow promotes the image by applying the regular manifests in `k8s/production` and then deletes the canary deployment. No manual intervention is required.
