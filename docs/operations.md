# Operations Procedures

## Secret Rotation

Secrets are stored in HashiCorp Vault and rotated automatically via the
`secret-rotation` CronJob. The job runs on the first day of every third
month and updates the database and JWT secrets.

Manual rotation can be performed with:
```bash
python scripts/vault_rotate.py
```
Pods will read the new values on the next request because the Vault
client caches secrets in memory. In emergency situations follow the
[break glass procedure](break_glass.md).
