# Service Ownership

This guide outlines expectations for owning a service in the Yosai Intel Dashboard.

## Responsibilities

- Maintain code, tests, documentation, and deployment manifests for the service.
- Monitor dashboards and alerts; keep SLOs up to date.
- Provide runbooks and ADRs for significant changes under `docs/runbooks` and `docs/adr`.
- Respond to incidents and drive post-incident reviews.

## On-call Expectations

1. Acknowledge alerts within five minutes and start investigation.
2. Consult relevant runbooks to guide remediation steps.
3. Escalate in `#ops-oncall` if the issue cannot be resolved within fifteen minutes.
4. Update the incident tracker with actions taken and outcomes.

## Handover

1. When transferring ownership, update CODEOWNERS and any service metadata.
2. Review existing ADRs and runbooks with the new owners.
3. Verify monitoring, alerts, and dashboards are configured for the new team.

## Resources

- [Runbooks](runbooks/)
- [Architecture Decision Records](adr/)
- [Developer Onboarding](developer_onboarding.md)
