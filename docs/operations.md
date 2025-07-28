# Operations Procedures

## Secret Rotation

Secrets are stored in HashiCorp Vault and rotated automatically via the
`secret-rotation` CronJob. The job runs on the first day of every third
month and updates the database and JWT secrets.

Manual rotation can be performed with:
```bash
python scripts/vault_rotate.py
```
Set `SECRET_INVALIDATE_URLS` to a comma-separated list of service
addresses before running the script. Each address should expose a
`/invalidate-secret` endpoint that triggers `invalidate_secret()` so new
credentials are reloaded immediately:

```bash
export SECRET_INVALIDATE_URLS="http://dashboard:8050,http://analytics:8001"
python scripts/vault_rotate.py
```

In emergency situations follow the [break glass procedure](break_glass.md).

## Gateway Security Headers

The gateway adds several HTTP response headers to improve security:

- `Content-Security-Policy: default-src 'self'`
- `X-Frame-Options: DENY`
- `X-Content-Type-Options: nosniff`

These headers are applied globally by middleware and help prevent content injection attacks, framing vulnerabilities, and MIME type sniffing.
