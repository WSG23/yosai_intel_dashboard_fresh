# Secret Rotation

Secrets must be rotated regularly to reduce the risk of compromise. Each secret stores the timestamp of its last rotation in an environment variable named `<SECRET_NAME>_LAST_ROTATED` using ISO 8601 format.

## Checking rotation status

Run the helper script to verify that secrets meet rotation policy:

```bash
python deployment/scripts/check_secret_rotation.py
```

The deployment pipeline runs this check automatically during the `preflight` stage.

## Rotating a secret

1. Generate a new secret value and update the backing store (environment variable, secret store, etc.).
2. Restart any services that consume the secret.
3. Set `<SECRET_NAME>_LAST_ROTATED` to the current UTC timestamp.
4. Re-run the rotation check to confirm the secret is compliant.
