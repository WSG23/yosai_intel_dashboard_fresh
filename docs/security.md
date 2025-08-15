# Security Protections

This project implements safeguards aligned with the OWASP Top 10 categories.

## Injection

- Parameterized queries are required for all database access to avoid SQL injection.
- `SecurityValidator` applies `SQLRule` and `XSSRule` to block SQL injection
  and cross-site scripting payloads. HTML is sanitized with `bleach.clean`
  allowing only safe tags and attributes.

## Authentication

Authentication mechanisms enforce strong credential and session management. Tokens and session IDs are protected and validated on every request to minimize the risk of broken authentication.

### Auth Flow

Service-to-service calls use signed JWTs. Each token includes a `sub` claim identifying the calling service and may include an `aud` claim for the intended recipient. The `verify_jwt_token` helper decodes the token and validates:

- the signature and expiration (`exp`)
- presence of the `sub` claim
- optional audience matching when an `aud` value is supplied

Failures return HTTP 401 with specific error codes such as `token_expired` or `invalid_audience` to aid debugging and auditing.

### Roles

Access to gateway endpoints is controlled by roles defined in `config/rbac.yaml`.
The default roles are:

- **admin** – full access including door control and configuration changes
- **analyst** – read and write analytics data
- **viewer** – read-only analytics access
- **service** – enqueue and dequeue background tasks

Routes require specific permissions which are granted to roles via the matrix.
Requests presenting an `X-Roles` header with an appropriate role, or an
`X-Permissions` header with the explicit permission, are allowed.

Key gateway routes and their required roles are:

- `/api/v1/doors` – `admin`
- `/api/v1/analytics` – `admin`, `analyst`, or `viewer`
- `/api/v1/events` – `admin`
- `/admin` – `admin`

## Sensitive Data Exposure

Secrets and personal data are stored using encrypted channels and secret management tooling. Configuration files avoid embedding credentials directly and rely on secure storage.

## Insecure Deserialization

`InsecureDeserializationRule` rejects input containing patterns such as `pickle.loads` or YAML object tags that could trigger unsafe object deserialization.

## Server-Side Request Forgery (SSRF)

`SSRFRule` blocks URLs referencing internal hosts (e.g., `127.0.0.1`, `169.254.169.254`, `10.x.x.x`) or dangerous schemes like `file://`, reducing the risk of internal network access.

## Secure Database Queries

To reduce the risk of SQL injection vulnerabilities:

- Always use parameterized queries with placeholders like `%s` or `?` rather than formatting values into query strings.
- Prefer the `execute_query` and `execute_command` helpers which enforce parameter validation.
- Use `SecureQueryBuilder.build_select` to assemble `SELECT` statements with
  allow-listed tables and columns.
- Never concatenate untrusted input with SQL keywords or table names.
- Validate user-supplied data types before executing a query.

Following these practices ensures that user input is passed separately from the SQL statement, preventing malicious injections.

## Secret Rotation

Secrets are rotated automatically. The `k8s/cron/secret-rotate.yaml` CronJob
invokes a Vault script to generate fresh credentials via the KMS policies in
`vault/policies/` and then updates the Kubernetes secret objects. Running
services read credentials from mounted files and either use the
`deployment/reload-secrets.sh` helper (which sends `HUP` to the process) or the
`pkg/config` `SecretWatcher` to pick up changes as Kubernetes replaces the
files.

To trigger a rotation manually, run:

```bash
kubectl create job --from=cronjob/secret-rotate secret-rotate-manual
```
