# Vault Integration

The dashboard retrieves all sensitive credentials from HashiCorp Vault.

## Deployment

A StatefulSet under `k8s/vault` provisions a three node Vault cluster.
Pods authenticate using a token provided via `vault-secret` and the
address from `vault-config`.

## Policies

Example policies are located in `vault/policies`. Each service receives a
policy granting read access to its own secret path.

## Rotation

The `secret-rotation` CronJob updates the database and JWT secrets every
90 days using `scripts/vault_rotate.py`.

## Audit Logging

`services/common/vault_client.py` logs every secret read. Enable Vault's
built-in audit devices to collect a complete trail of access events.
