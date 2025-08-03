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

### Timescale Replication

`scripts/replicate_to_timescale.py` exports the metric `replication_lag_seconds`
to track how far the TimescaleDB copy lags behind the primary database. The
alert rule defined in `monitoring/alerts.yml` fires when this value exceeds
60&nbsp;seconds for five minutes.

### CPU & Memory Alerts

Prometheus also records CPU and memory usage for each pod. Edit
`monitoring/prometheus/rules/app_alerts.yml` to trigger alerts when resource
limits are approached. Example rules:

```yaml
- alert: CPUHighUsage
  expr: avg(rate(container_cpu_usage_seconds_total[5m])) by (pod) > 0.8
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: Pod CPU usage above 80% for 5 minutes
- alert: MemoryHighUsage
  expr: container_memory_usage_bytes{image!=""} /
    container_spec_memory_limit_bytes{image!=""} > 0.9
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: Pod memory usage above 90% of limit
```

### Connection Pool Monitoring

Database connection pool health is exported via Prometheus metrics:

- `db_pool_current_size` – current maximum pool size
- `db_pool_active_connections` – connections in use
- `db_pool_wait_seconds` – histogram of wait time to obtain a connection

Example queries:

```promql
db_pool_active_connections
histogram_quantile(0.95, rate(db_pool_wait_seconds_bucket[5m]))
```

Set alerts if active connections approach the pool size or wait times grow.

Import `monitoring/grafana/dashboards/unified-platform.json` into Grafana to view
CPU and memory graphs based on these metrics.

## Performance Dashboards

Prometheus scrapes metrics from `/metrics` using the sample
`monitoring/prometheus.yml`. Import this data source into Grafana to build CPU,
memory and request charts. Logs can be forwarded to Elasticsearch through
`logging/logstash.conf` and visualized with Kibana.

## Database Connection Logging

The database connection factory logs warnings whenever connection attempts are
retried and records errors if all retries are exhausted. The connection pool
also emits warnings when it expands or drops unhealthy connections, including
current pool sizes. Operators should monitor these log messages to diagnose
connectivity issues early.

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

## Zero Downtime Updates

The dashboard can be updated without service interruption using either rolling or blue/green deployments.

### Rolling Update

Kubernetes performs a rolling update when the container image of a deployment is changed. New pods are created gradually while the old ones are terminated only after the new pods pass their readiness checks. You can monitor progress and pause if needed.

```bash
# replace the image tag to trigger a rolling update
kubectl set image deployment/yosai-dashboard yosai-dashboard=registry.example.com/yosai-dashboard:<new-tag> -n yosai-dev
kubectl rollout status deployment/yosai-dashboard -n yosai-dev
```

To pause the rollout and check health before continuing:

```bash
kubectl rollout pause deployment/yosai-dashboard -n yosai-dev
# inspect pods or run smoke tests here
kubectl rollout resume deployment/yosai-dashboard -n yosai-dev
```

### Blue/Green

Blue/green deployments run the new version alongside the old one. The manifests under `k8s/bluegreen` define two deployments and a service that targets a `color` label. Deploy the new color and switch the service when ready:

```bash
kubectl apply -f k8s/bluegreen/dashboard-green.yaml
kubectl rollout status deployment/yosai-dashboard-green
# move 10% of traffic for a quick smoke test
kubectl scale deployment/yosai-dashboard-green --replicas=1
kubectl scale deployment/yosai-dashboard-blue --replicas=9
# switch all traffic to green
kubectl patch service yosai-dashboard -p '{"spec":{"selector":{"app":"yosai-dashboard","color":"green"}}}'
```

A Helm release can use the same technique:

```bash
helm upgrade yosai-intel ./helm/yosai-intel \
  --set image.tag=<new-tag> --set color=green
```

### Rollback Procedures

If the new deployment fails its health checks, revert immediately using one of
the following options:

#### Automated rollback

```bash
kubectl rollout undo deployment/yosai-dashboard -n yosai-dev
kubectl rollout status deployment/yosai-dashboard -n yosai-dev
```

#### Manual rollback script

```bash
./rollback.sh [service] [namespace]
```

The script switches the service selector between blue and green deployments. It
defaults to the `yosai-dashboard` service in the `default` namespace.

#### Manual image reversion

```bash
kubectl set image deployment/yosai-dashboard \
  yosai-dashboard=ghcr.io/wsg23/yosai-dashboard:<previous-tag> -n yosai-dev
kubectl rollout status deployment/yosai-dashboard -n yosai-dev
```

Then scale down or delete the faulty pods once the service is stable.


## Enabling Microservice Manifests

YAML manifests for each microservice reside in `k8s/services`. Apply them to
create the Deployment, standard `Service`, and headless `Service` objects:

```bash
kubectl apply -f k8s/services/analytics-service.yaml
kubectl apply -f k8s/services/api-gateway.yaml
kubectl apply -f k8s/services/event-ingestion.yaml
```

The directory also contains example templates for blue/green and canary
strategies using Istio `VirtualService` weight rules. Adjust the weights and
apply the files when performing controlled rollouts:

```bash
kubectl apply -f k8s/services/bluegreen-template.yaml
kubectl apply -f k8s/services/canary-template.yaml
```

To enable mTLS between services, adapt the `k8s/services/mtls-snippet.yaml`
configuration. It mirrors the `ISTIO_MUTUAL` settings from
`k8s/istio/destination-rules.yaml`.
