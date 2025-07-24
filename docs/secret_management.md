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

Ensure these values are defined before starting the application. The API
raises a `RuntimeError` if `SECRET_KEY` is not set. When
`YOSAI_ENV=production` the configuration validation step will also refuse
to start if `DB_PASSWORD` is missing.

## Rotation Procedures

1. Generate a new secret using your preferred password manager.
2. Update the value in your environment or secret store.
3. Restart or redeploy the application so the new secret is loaded.
4. Revoke any credentials that were replaced, such as old Auth0
   application secrets or database passwords.

Routine rotation should be scheduled at least every 90 days or according
to your organization policy.

### Rotation Script

The helper `scripts/rotate_secrets.py` automates these steps. Run it from
the repository root:

```bash
python scripts/rotate_secrets.py
```

The script generates new values for `SECRET_KEY` and any database
passwords in `k8s/config/api-secrets.yaml`. If `kubectl` can reach your
cluster, the updated manifest is applied automatically. After the pods
restart, remove the previous credentials from your secret store or
database to prevent reuse.

## Docker and Cloud Secret Usage

Secrets can be supplied as Docker secrets when running with Docker
Compose. Provide `DB_PASSWORD` and `SECRET_KEY` via environment
variables or create `secrets/db_password.txt` and `secrets/secret_key.txt`
locally so Docker mounts them under `/run/secrets`. **Do not commit
these files.** You can also rely on the `ConfigManager` to load them from
your secret backend. For cloud deployments the `SecretManager` supports
`env`, `aws`, and `vault` backends. Set the `SECRET_BACKEND` variable to
select the desired provider.

When using the `aws` backend the application reads secrets from AWS
Secrets Manager. The configured AWS credentials and region are used to
fetch the secret with a name matching the requested key. With the
`vault` backend the client connects to HashiCorp Vault using the
`VAULT_ADDR` and `VAULT_TOKEN` environment variables. Keys may include a
field selector like `secret/data/db#password` to read specific values.

### AWS Secrets Manager Configuration

`SecureConfigManager` also understands strings starting with `"aws-secrets:"`.
Install the `boto3` package and ensure the AWS SDK can locate credentials and
region configuration. Secrets are retrieved using the configured name and the
plain string value is injected into the loaded configuration. Missing secrets or
authentication issues raise a `ConfigurationError` with details about the
problem. Example usage:

```yaml
database:
  password: aws-secrets:prod/db_password
security:
  secret_key: aws-secrets:prod/app_secret
```

### Vault Configuration

The optional `SecureConfigManager` resolves any string starting with
`"vault:"` in the YAML configuration. Install the `hvac` and
`cryptography` packages and set the following environment variables:

```
VAULT_ADDR=https://vault.example.com
VAULT_TOKEN=s.xxxxxx
FERNET_KEY=<base64-fernet-key>
```

`VAULT_ADDR` and `VAULT_TOKEN` authenticate the Vault client. `FERNET_KEY`
is used to decrypt any encrypted values returned from Vault. The
`SecureConfigManager` will raise a `ConfigurationError` if either credential is
missing or if a secret cannot be retrieved.
Update `production.yaml` to reference secrets like:

```yaml
database:
  password: vault:secret/data/db#password
security:
  secret_key: vault:secret/data/app#secret_key
```

Create the manager with:

```python
from config import SecureConfigManager

cfg = SecureConfigManager()
```

### Local Development with Vault

For local development a Vault dev server can be used. Start Vault with:

```bash
vault server -dev
```

The services default to `http://127.0.0.1:8200` and token `root` when
`YOSAI_ENV` is set to `development`. In production deployments
`VAULT_ADDR` and `VAULT_TOKEN` must be provided via environment variables
or the accompanying Kubernetes `ConfigMap` and `Secret` manifests.

Secrets are fetched through `services.common.secrets.get_secret()` which
uses an in-memory cache. Call `invalidate_secret()` after rotating a
value to force a reload.

## Incident Handling

If you suspect a secret has been exposed:

1. Rotate the affected secret immediately following the procedure above.
2. Audit application logs for suspicious activity.
3. Revoke any tokens or credentials that may have been compromised.
4. Investigate the source of the leak and update processes to prevent
   recurrence.

For major incidents follow your organizational incident response plan and
notify the security team.
