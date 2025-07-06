# Secret Management

This guide covers how secrets are handled in the Yōsai Intel Dashboard.

## Required Secrets

The application expects several secrets to be provided via environment
variables, Docker secrets, or a cloud secret manager:

- `SECRET_KEY` – Flask and Dash session signing key
- `DB_PASSWORD` – database account password
- `AUTH0_CLIENT_ID` – Auth0 application identifier
- `AUTH0_CLIENT_SECRET` – Auth0 client secret
- `AUTH0_DOMAIN` – Auth0 domain used for OIDC
- `AUTH0_AUDIENCE` – expected API audience

Ensure these values are defined before starting the application. When
`YOSAI_ENV=production` the configuration validation step will refuse to
start if `SECRET_KEY` or `DB_PASSWORD` is missing.

## Rotation Procedures

1. Generate a new secret using your preferred password manager.
2. Update the value in your environment or secret store.
3. Restart or redeploy the application so the new secret is loaded.
4. Revoke any credentials that were replaced, such as old Auth0
   application secrets or database passwords.

Routine rotation should be scheduled at least every 90 days or according
to your organization policy.

## Docker and Cloud Secret Usage

Secrets can be supplied as Docker secrets when running with Docker
Compose. The production compose file expects `secrets/db_password.txt`
and `secrets/secret_key.txt` which are mounted under `/run/secrets`. The
application reads these files and exposes them through environment
variables. For cloud deployments the
`SecretManager` supports `env`, `aws`, and `vault` backends. Set the
`SECRET_BACKEND` variable to select the desired provider.

When using the `aws` backend the application reads secrets from AWS
Secrets Manager. The configured AWS credentials and region are used to
fetch the secret with a name matching the requested key. With the
`vault` backend the client connects to HashiCorp Vault using the
`VAULT_ADDR` and `VAULT_TOKEN` environment variables. Keys may include a
field selector like `secret/data/db#password` to read specific values.

## Incident Handling

If you suspect a secret has been exposed:

1. Rotate the affected secret immediately following the procedure above.
2. Audit application logs for suspicious activity.
3. Revoke any tokens or credentials that may have been compromised.
4. Investigate the source of the leak and update processes to prevent
   recurrence.

For major incidents follow your organizational incident response plan and
notify the security team.
