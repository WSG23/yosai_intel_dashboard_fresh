# Clean Architecture Migration Runbook

## Diagnosing Import Issues
- Check `structure_validation_status` gauge in Prometheus.
- Inspect application logs for `ImportError` or `ModuleNotFoundError`.
- Verify symlinks for legacy imports remain intact.

## Common Problems and Solutions
- **Missing module**: run `scripts/update_imports.py` and redeploy.
- **Legacy import used**: identify caller from `legacy_import_usage_total` metric and refactor to new module.
- **Validation failures**: execute `scripts/validate_structure.py` to locate violations.

## Performance Troubleshooting
- Examine `import_resolution_seconds:p95` for spikes.
- Compare `api_response_time_p95:5m` between previous and current versions.
- Review system CPU and memory panels in Grafana.

## Contact Information
- DevOps On-Call: devops@example.com
- Architecture Team: architecture@example.com
- Slack: #yosai-ops
