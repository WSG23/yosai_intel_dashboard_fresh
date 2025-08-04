# Security Protections

This project implements safeguards aligned with the OWASP Top 10 categories.

## Injection

- Parameterized queries are required for all database access to avoid SQL injection.
- `SecurityValidator` applies `SQLRule` and `XSSRule` to block SQL injection and cross-site scripting payloads.

## Authentication

Authentication mechanisms enforce strong credential and session management. Tokens and session IDs are protected and validated on every request to minimize the risk of broken authentication.

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
