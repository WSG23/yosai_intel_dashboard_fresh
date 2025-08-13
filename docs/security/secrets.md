# Secret Rotation and mTLS Procedures

## Rotation Schedule

Secrets are automatically rotated weekly via the `Rotate Secrets` GitHub Actions workflow. Rotation occurs every Sunday at 03:00 UTC and updates Kubernetes manifests and Vault entries.

## Emergency Rotation

1. Ensure `VAULT_ADDR` and `VAULT_TOKEN` environment variables are set.
2. Run `python scripts/rotate_secrets.py` from the repository root.
3. Commit and deploy the updated manifests if required.

## mTLS Certificates

Shared secrets have been replaced with mTLS certificates issued through SPIRE and Vault PKI. Services read certificates from `/run/secrets/tls` mounted by the Vault agent.

## Contact

For security incidents or further questions, reach out to the security team.
