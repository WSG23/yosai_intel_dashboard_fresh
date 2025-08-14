# Deployment Runbook

## Rollout Procedure
1. Build and push container images.
2. Deploy the canary release using `k8s/canary` manifests.
3. Verify metrics and logs for the canary pods.
4. Start `scripts/rollback.sh` to watch unlock latency and error SLOs. The script queries
   Prometheus and will undo the rollout if P95 latency exceeds **100 ms** for 5 minutes or
   errors exceed **1%**.
5. Confirm log entries appear in the staging ELK and Datadog dashboards and include correlation IDs from test requests.
6. Promote traffic with the blue/green deployment in `k8s/bluegreen`.
7. Remove the old color once the new version is healthy.

## Rollback Procedure
1. Re-route traffic back to the previous color or disable the canary.
2. Redeploy the last known good image or run `scripts/rollback.sh <deployment> <namespace>`
   to trigger `kubectl rollout undo` when SLOs are violated.
3. Monitor until service health is restored.
