# Service Mesh Evaluation

This document summarizes the current Linkerd setup and when it may be worth keeping or removing the service mesh.

## Current Configuration

Linkerd manifests live under `k8s/linkerd/`:

- `traffic-split.yaml` splits traffic for the `yosai-dashboard` service, sending 90% to `yosai-dashboard-v1` and 10% to `yosai-dashboard-v2`.
- `service-profile.yaml` marks `GET /api` requests as retryable and defines a retry budget with a 20% ratio, 10 minimum retries per second and a 10&nbsp;s TTL.
- `circuit-breaker.yaml` configures failure accrual to trip the circuit after 5 consecutive failures within a 1&nbsp;minute window.

## Benefits

- **Traffic shaping** – Weighted splits enable canary or blue/green deployments without modifying application code.
- **Automated retries** – Service profiles allow idempotent routes to be retried when transient errors occur.
- **Circuit breaking** – Failure accrual prevents cascading failures by temporarily halting requests to an unhealthy backend.

## Operational Costs

Running Linkerd introduces additional components and sidecars that consume CPU and memory. The control plane must be upgraded and monitored, certificates renewed and mTLS maintained. Small clusters or simple setups may find the overhead disproportionate to the benefits.

## Recommendations

### Keep Linkerd when

- You need canary releases or fine‑grained traffic routing.
- Automatic retries and circuit breaking improve reliability.
- Observability and mTLS provided by the mesh justify the extra complexity.

### Remove Linkerd when

- The application runs as a single stable service without complex rollout strategies.
- Resource limits or operational simplicity are higher priorities than advanced routing features.

To remove Linkerd delete the manifests in `k8s/linkerd/` and uninstall the Linkerd control plane.
