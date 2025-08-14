# Vault Key Rotation Runbook

## Scheduled Rotation
1. A Kubernetes CronJob (`vault-key-rotation`) runs nightly and calls the Vault rotation API.
2. The job posts to `$VAULT_ADDR/v1/sys/rotate` with the cluster's `VAULT_TOKEN`.
3. On success the API returns `204` and rotates the underlying encryption keys.

## Manual Rotation
1. Ensure `VAULT_ADDR` and `VAULT_TOKEN` environment variables are set.
2. Trigger the CronJob manually:
   ```bash
   kubectl create job --from=cronjob/vault-key-rotation vault-key-rotation-manual
   ```
3. Check the job status until completion:
   ```bash
   kubectl get jobs | grep vault-key-rotation-manual
   ```
4. Confirm Vault reports the new key version:
   ```bash
   curl -H "X-Vault-Token: $VAULT_TOKEN" "$VAULT_ADDR/v1/sys/rotations" | jq
   ```

## Validation
- Ensure the CronJob logs show a `204` response from the rotation API.
- Verify dependent services continue to authenticate and decrypt data after rotation.
- Investigate and rollback if any service fails to access Vault post-rotation.
