# Security Configuration

This guide outlines how to configure security-sensitive settings for the Yōsai Intel Dashboard. It covers environment variables, secret management, transport security, and browser hardening.

## Required Environment Variables

Provide the following variables before starting the application:

- `JWT_SECRET_KEY` – key used to sign and validate JSON Web Tokens.
- `DB_HOST`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` – database connection credentials.
- `REDIS_URL` – connection string for caching and session storage.
- `VAULT_ADDR`, `VAULT_TOKEN` – address and token for accessing HashiCorp Vault when used.
- `SSL_CERT_FILE`, `SSL_KEY_FILE` – paths to TLS certificate and private key when terminating TLS in the application.

## Secret Management

Secrets should never be committed to the repository. Use one of the following mechanisms:

- **HashiCorp Vault** – store credentials centrally and inject them at runtime using `VAULT_ADDR` and `VAULT_TOKEN`. Applications fetch secrets via Vault's API or mounted files.
- **Kubernetes Secrets** – for clusters, store secrets in `Secret` resources and mount them as environment variables or files. Combine with Vault using the [Vault Agent Injector](https://developer.hashicorp.com/vault/docs/platform/k8s/injector) for automated secret retrieval.

Rotate secrets regularly and restrict access using least-privilege policies.

## TLS/SSL Setup

- Use TLS to encrypt all traffic. When running behind a reverse proxy like NGINX or an ingress controller, terminate TLS there and forward traffic over HTTPS.
- Obtain certificates from a trusted Certificate Authority (e.g., Let's Encrypt) and configure automatic renewal.
- Enable HTTP Strict Transport Security (HSTS) and disable weak ciphers and protocols.

## CORS and CSP Recommendations

- Set `Access-Control-Allow-Origin` only to trusted domains.
- Allow only required HTTP methods and headers.
- Use a restrictive Content Security Policy, e.g., `default-src 'self'; frame-ancestors 'none'; script-src 'self'`.

## Example Configuration

### Local Development (`.env`)

```env
JWT_SECRET_KEY=local-dev-secret
DB_HOST=localhost
DB_USER=app_user
DB_PASSWORD=secret
DB_NAME=yosai
REDIS_URL=redis://localhost:6379/0
VAULT_ADDR=http://localhost:8200
VAULT_TOKEN=dev-token
```

Run the backend with `FLASK_ENV=development` and use self-signed certificates if TLS is required locally.

### Production (Kubernetes + Vault)

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
stringData:
  DB_USER: app_user
  DB_PASSWORD: ${DB_PASSWORD}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: yosai-api
spec:
  template:
    spec:
      serviceAccountName: vault-auth
      containers:
          - name: api
            image: registry.example.com/yosai:0.1.0

          env:
            - name: JWT_SECRET_KEY
              valueFrom:
                secretKeyRef:
                  name: jwt-secret
                  key: JWT_SECRET_KEY
          volumeMounts:
            - name: tls
              mountPath: /tls
      volumes:
        - name: tls
          secret:
            secretName: tls-cert
```

Ingress controllers should terminate TLS using certificates stored as secrets, and CORS/CSP headers should be applied at the edge.
