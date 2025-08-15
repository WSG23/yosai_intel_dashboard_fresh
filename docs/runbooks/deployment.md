# Deployment Runbook

## Rollout Procedure
1. Build and push container images.
2. Trigger the `canary` stage in `deployment/pipeline.yaml` or run `kubectl apply -f k8s/canary` to deploy the canary release.
3. Verify metrics and logs for the canary pods. Readiness and liveness probes should remain green before continuing.
4. Start `scripts/rollback.sh` to watch unlock latency and error SLOs. The script queries
   Prometheus and will undo the rollout if P95 latency exceeds **100 ms** for 5 minutes or
   errors exceed **1%**.
5. Confirm log entries appear in the staging ELK and Datadog dashboards and include correlation IDs from test requests.
6. Execute the `blue_green` stage to shift traffic using `k8s/bluegreen` manifests.
7. Remove the old color once the new version is healthy.

## Rollback Procedure
1. Re-route traffic back to the previous color or disable the canary.
2. Run `scripts/rollback.sh <deployment> <namespace>` or `kubectl rollout undo` to revert to the last known good image when SLOs are violated.
3. Monitor until service health is restored.
