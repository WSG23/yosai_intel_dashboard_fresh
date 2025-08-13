> **Note**: Import paths updated for clean architecture. Legacy imports are deprecated.

# Secret Management

This guide covers how secrets are handled in the Yōsai Intel Dashboard.

## Required Secrets

The application expects several secrets to be provided via environment
variables, Docker secrets, or a cloud secret manager:

Avoid hard coding these values in code or configuration files. Generate
them dynamically with `os.urandom` during testing or store them securely
in your secret backend.

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

## Secure Factory Integration

The configuration factory (`create_config_manager`) uses the
`SecureConfigManager` to resolve `vault:` and `aws-secrets:` references
before services start. Database managers consume the retrieved credentials
and scrub passwords from connection errors so sensitive values never
appear in logs.

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

### Retrieving Rotated Secrets

`scripts/vault_rotate.py` updates the values stored in Vault without
printing them to the terminal. Fetch the new credentials using the Vault
CLI or another authenticated client:

```bash
vault kv get -field=password secret/data/db
vault kv get -field=secret secret/data/jwt
```

Share the retrieved secrets only over secure channels and update any
dependent services accordingly.

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

## Kubernetes Secrets

The `k8s/base/secrets.yaml` file in the repository is provided only as a
template. It contains placeholder values such as `<managed-secret>` so that
real credentials are never stored in Git. Supply the actual values using your
deployment pipeline or reference a sealed secret created by your cluster's
secret manager. Patch the manifest at deploy time or mount the secrets from an
external system to keep them out of version control.

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
from yosai_intel_dashboard.src.infrastructure.config import SecureConfigManager

cfg = SecureConfigManager()
```

### Local Development with Vault

For local development a Vault dev server can be used. Start Vault with:

```bash
vault server -dev
```

The services default to `http://127.0.0.1:8200` when `YOSAI_ENV` is set to
`development`. Provide `VAULT_TOKEN` explicitly using the token printed by
the dev server. In all deployments `VAULT_ADDR` and `VAULT_TOKEN` must be
supplied via environment variables or the accompanying Kubernetes
`ConfigMap` and `Secret` manifests.

Secrets are fetched through `yosai_intel_dashboard.src.services.common.secrets.get_secret()` which
uses an in-memory cache. Call `invalidate_secret()` after rotating a
value to force a reload.

### Creating Secrets in Vault

To store secrets centrally create a path for the dashboard in Vault. The
default examples assume the KV engine is mounted at `secret`:

```bash
vault kv put secret/data/yosai \
  SECRET_KEY="$(openssl rand -base64 32)" \
  DB_PASSWORD="change-me" \
  AUTH0_CLIENT_ID="<client-id>" \
  AUTH0_CLIENT_SECRET="<client-secret>" \
  AUTH0_DOMAIN="example.auth0.com" \
  AUTH0_AUDIENCE="https://api.example.com"
```

Reference these fields from your configuration using the `vault:` prefix:

```yaml
security:
  secret_key: vault:secret/data/yosai#SECRET_KEY
database:
  password: vault:secret/data/yosai#DB_PASSWORD
auth0:
  client_id: vault:secret/data/yosai#AUTH0_CLIENT_ID
  client_secret: vault:secret/data/yosai#AUTH0_CLIENT_SECRET
  domain: vault:secret/data/yosai#AUTH0_DOMAIN
  audience: vault:secret/data/yosai#AUTH0_AUDIENCE
```

### Environment Overrides

Environment variables override values from YAML after secrets are
resolved. Set variables to a `vault:` URI to fetch them directly from
Vault:

```bash
export VAULT_ADDR=https://vault.example.com
export VAULT_TOKEN=s.xxxxxx
export SECRET_BACKEND=vault

export SECRET_KEY=vault:secret/data/yosai#SECRET_KEY
export DB_PASSWORD=vault:secret/data/yosai#DB_PASSWORD
export AUTH0_CLIENT_ID=vault:secret/data/yosai#AUTH0_CLIENT_ID
export AUTH0_CLIENT_SECRET=vault:secret/data/yosai#AUTH0_CLIENT_SECRET
export AUTH0_DOMAIN=vault:secret/data/yosai#AUTH0_DOMAIN
export AUTH0_AUDIENCE=vault:secret/data/yosai#AUTH0_AUDIENCE

python start_api.py  # unified startup script
```

## Incident Handling

If you suspect a secret has been exposed:

1. Rotate the affected secret immediately following the procedure above.
2. Audit application logs for suspicious activity.
3. Revoke any tokens or credentials that may have been compromised.
4. Investigate the source of the leak and update processes to prevent
   recurrence.

For major incidents follow your organizational incident response plan and
notify the security team.
