# Operations Procedures

## Secret Rotation

The dashboard retrieves sensitive credentials from Kubernetes Secrets. To rotate a secret:

1. Generate a new credential using your password manager or cloud secret tooling.
2. Update the manifest under `k8s/config/api-secrets.yaml` with the new values.
3. Apply the secret with `kubectl apply -f k8s/config/api-secrets.yaml`.
4. Restart the deployment so pods pick up the updated secret:
   ```bash
   kubectl rollout restart deployment/yosai-dashboard -n yosai-dev
   ```
5. Verify the application functions correctly and then revoke the old credentials.

Regular rotation every 90 days is recommended.
