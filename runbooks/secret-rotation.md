# Secret Rotation Runbook

## Manual Rotation
1. Ensure you have access to Vault or AWS Secrets Manager and a configured Kubernetes context if applying changes.
2. Export the required environment variables:
   - `VAULT_ADDR` and `VAULT_TOKEN` for Vault access, or
   - `AWS_REGION` for AWS Secrets Manager.
3. From the repository root, run the rotation script:
   ```bash
   python scripts/rotate_secrets.py
   ```
4. Commit the updated `k8s/config/api-secrets.yaml` file and push to the main branch:
   ```bash
   git commit -am "chore: rotate secrets"
   git push
   ```
5. Verify the deployment has restarted and is using the new secrets.
