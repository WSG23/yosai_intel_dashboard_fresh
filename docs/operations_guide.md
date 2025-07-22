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

## Zero-Downtime Updates

For full releases we perform either a rolling update or a blue/green switch. Both methods keep
the service available while new pods start and pass health checks.

### Rolling Update

Kubernetes handles rolling updates natively. Update the deployment with the new
image and monitor the rollout status:

```bash
kubectl set image deployment/yosai-dashboard yosai-dashboard=yosai-intel-dashboard:<new-tag>
kubectl rollout status deployment/yosai-dashboard
```

Pods are replaced gradually based on the deployment strategy. If the new
version fails readiness or liveness probes you can roll back with:

```bash
kubectl rollout undo deployment/yosai-dashboard
```

### Blue/Green Switch

Manifests under `k8s/bluegreen` deploy parallel `blue` and `green` deployments
alongside a shared service. Start the new color, wait for all pods to become
ready and then patch the service selector to shift traffic:

```bash
# deploy the new color
kubectl apply -f k8s/bluegreen/dashboard-green.yaml

# direct the service to the green deployment
kubectl patch service yosai-dashboard -p '{"spec":{"selector":{"app":"yosai-dashboard","color":"green"}}}'
```

If problems appear after the switch, revert the service selector to the previous
color and delete the failed deployment:

```bash
kubectl patch service yosai-dashboard -p '{"spec":{"selector":{"app":"yosai-dashboard","color":"blue"}}}'
kubectl delete -f k8s/bluegreen/dashboard-green.yaml
```

## Secret Rotation

Secrets used by the dashboard are rotated automatically via the **Rotate Secrets**
workflow. This job runs every Sunday at **03:00 UTC** for the staging environment
and **03:30 UTC** for production. After new credentials are generated with
`scripts/rotate_secrets.py`, the deployment is restarted so pods reload the
updated secrets.

If a rotation fails or you need to recover manually, run the script locally and
restart the deployment:

```bash
python scripts/rotate_secrets.py
kubectl rollout restart deployment/yosai-dashboard -n yosai-dev
```

Verify the pods become healthy and the application functions correctly before
revoking any previous credentials.

