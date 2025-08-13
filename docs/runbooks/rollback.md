# Rollback Runbook

This runbook describes how to revert a deployment using the canary strategy and rollback scripts.

## Canary Release Validation
1. Deploy the canary chart via ArgoCD which routes approximately 10% of traffic to the new version.
2. Monitor metrics and logs in Grafana and Prometheus.
3. If no SLO breaches occur, proceed with full rollout.

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

## Automated Rollback on SLO Breach
The CI pipeline runs a check that calls `scripts/rollback/auto_rollback.sh`. If the error rate exceeds the threshold, the deployment is automatically rolled back.
