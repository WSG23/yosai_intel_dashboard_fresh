# Break Glass Procedure

If Vault becomes unavailable or secrets are corrupted, temporary credentials can be injected manually.

1. Generate replacement secrets for the affected services.
2. Create a Kubernetes secret `emergency-secrets` with the values.
3. Patch the deployments to mount this secret and set the appropriate environment variables.
4. Remove the patch once Vault is restored and rotate the credentials again.

All actions must be logged and reviewed by the security team.
