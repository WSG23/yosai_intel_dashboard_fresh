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

### Rollback

If the new deployment fails its health checks, revert immediately:

```bash
# send traffic back to the previous deployment
kubectl patch service yosai-dashboard -p '{"spec":{"selector":{"app":"yosai-dashboard","color":"blue"}}}'
# rollback the deployment to the previous replica set
kubectl rollout undo deployment/yosai-dashboard -n yosai-dev
# or use the provided helper script
scripts/rollback.sh
```

Then scale down or delete the faulty pods once the service is stable.

