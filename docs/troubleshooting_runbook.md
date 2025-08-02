# Troubleshooting Runbook

This runbook documents common operational failures and the steps to mitigate them.

## Pod Crash Loops

**Symptoms**: Pods repeatedly restart and `kubectl get pods` shows a `CrashLoopBackOff` status.

**Mitigation Steps**:
1. Inspect events and logs:
   ```bash
   kubectl describe pod <pod-name>
   kubectl logs <pod-name> --previous
   ```
2. Identify configuration or image errors and update values in the Helm chart or container image.
3. Redeploy the affected component:
   ```bash
   kubectl delete pod <pod-name>
   argocd app sync yosai-dashboard
   ```

## Failed Migrations

**Symptoms**: Deployments fail during startup because database migrations did not complete.

**Mitigation Steps**:
1. Review the migration job logs:
   ```bash
   kubectl logs job/<migration-job>
   ```
2. Run the migration manually if necessary:
   ```bash
   kubectl exec -it <migration-pod> -- alembic upgrade head
   ```
3. If migrations continue to fail, roll back to the previous release and investigate the schema state.

## Secret Sync Issues

**Symptoms**: Applications cannot access required secrets or ArgoCD reports `OutOfSync` on secret resources.

**Mitigation Steps**:
1. Check that the secret management sidecar or controller is running.
2. Re-run secret synchronization:
   ```bash
   argocd app sync yosai-dashboard --resource secrets
   ```
3. Validate access to the secret backend (e.g., Vault) and ensure the Kubernetes service account has correct permissions.

