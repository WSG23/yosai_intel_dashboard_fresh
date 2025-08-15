# Rollback Runbook

This runbook describes how to revert a deployment using the canary strategy and rollback scripts.

## Canary Release Validation
1. Deploy the canary chart via ArgoCD which routes approximately 10% of traffic to the new version.
2. Monitor metrics and logs in Grafana and Prometheus.
3. If no SLO breaches occur, proceed with full rollout.

## Automated Rollback

1. After each deployment, the pipeline records the current image tag and
   migration level as the `rollback-state` artifact.
2. If the deploy job fails or SLOs are violated, the pipeline calls
   `scripts/rollback/auto_rollback.sh` to restore the previous release.
3. No manual intervention is required for this path.

## Manual Rollback

Use this procedure if the automated rollback does not trigger or a specific
release must be reverted.

1. Download the latest `rollback-state` artifact from the CI interface.
2. Confirm `deployment/rollback_state.json` contains the desired image tag and
   migration level.
3. Run the rollback script with the target deployment and namespace:

   ```bash
   bash deployment/scripts/rollback.sh <deployment> <namespace>
   ```

4. Monitor the rollout status until completion:

   ```bash
   kubectl rollout status deployment/<deployment> -n <namespace>
   ```

5. Validate the service:

   - Run smoke tests against the service endpoint.
   - Check monitoring dashboards to ensure error rates and latency return to
     baseline.

6. Record the rollback in the incident tracker and create follow-up tasks.

## Rolling Back Images
Use the image rollback script to restore the previous container image:

```bash
scripts/rollback/restore_images.sh <deployment> <namespace>
```

## Restoring the Database
Provide a backup file and database connection string:

```bash
DB_DSN=postgres://user:pass@db:5432/yosai ./scripts/rollback/restore_database.sh backup.sql
```
