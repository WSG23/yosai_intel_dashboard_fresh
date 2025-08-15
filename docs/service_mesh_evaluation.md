# Service Mesh Evaluation

This document summarizes the current Linkerd setup and when it may be worth keeping or removing the service mesh.

## Current Configuration

Linkerd manifests live under `k8s/linkerd/`:

- `traffic-split.yaml` splits traffic for the `yosai-dashboard` service, sending 90% to `yosai-dashboard-v1` and 10% to `yosai-dashboard-v2`.
- `service-profile.yaml` marks `GET /api` requests for the dashboard as retryable and defines a retry budget with a 20% ratio, 10 minimum retries per second and a 10&nbsp;s TTL.
- `service-profile-api-gateway.yaml` applies the same retry logic to the `api-gateway` service.
- `service-profile-analytics-service.yaml` applies the same retry logic to the `analytics-service` service.
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

## Migration to Istio

The project now uses [Istio](https://istio.io) for service mesh features. The manifests under `k8s/istio/` enable:

- Automatic mTLS for all services
- Circuit breaking and retry policies via destination rules
- Canary deployments using `VirtualService` weight-based routing
- Integration with Jaeger and Grafana for tracing and metrics

Istio is first rolled out in non-production namespaces and then promoted to production once validated.

## Automatic mTLS

All pods injected with the Linkerd proxy automatically establish mutual TLS
(mTLS) when communicating with other meshed workloads. Certificates are issued by
the Linkerd identity service and rotated without any application changes.

### Verifying mTLS

Run `linkerd check --proxy` inside a proxy container to confirm it can obtain a
certificate and negotiate TLS. To inspect live traffic use `linkerd tap`; the
`tls=true` column indicates requests are encrypted:

```bash
kubectl exec deploy/yosai-dashboard -c linkerd-proxy -- \
  linkerd check --proxy
linkerd tap deploy/yosai-dashboard -n yosai-prod
```

### Certificate Rotation

Linkerd automatically rotates issuer certificates before expiry (24&nbsp;hours by
default). Check the current expiry time with `linkerd identity` and monitor the
`linkerd-identity` pod logs to ensure new certificates are issued regularly.

## Gaps After mTLS and Tracing

Implementing mutual TLS and distributed tracing outside of a mesh improves
security and observability but still leaves several capabilities unmanaged:

- Traffic policies and rate limiting are configured manually per service.
- Circuit breaking and retries are not uniformly enforced.
- Metrics collection lacks a consistent mesh-wide view.
- Progressive delivery (canary/blue‑green) requires custom scripting.

These gaps motivate evaluating a service mesh to centralize runtime policy and
telemetry.

## Linkerd vs. Istio Decision

| Capability | Linkerd | Istio |
|------------|---------|-------|
| Sidecar resource cost | Lower | Higher |
| Traffic management | Basic | Advanced (VirtualService, DestinationRule) |
| Policy enforcement | Limited | Rich RBAC and authorization policies |
| Ecosystem | Lean and simple | Extensive integrations and add‑ons |

Given the need for advanced traffic management and policy control, the project
will prototype **Istio** in the next phase.

## Non‑production Prototype and Benchmarking

1. Install Istio into a staging namespace:
   ```bash
   istioctl install --set profile=default
   kubectl label namespace staging istio-injection=enabled
   ```
2. Deploy a subset of services and generate load with tools like `k6` or `wrk`.
3. Record baseline latency and resource usage, then compare with mesh-enabled
   pods using Prometheus and `kubectl top`.
4. Document CPU, memory and p95 latency overhead to determine acceptable limits.

## Adoption Plan and Rollback Strategy

1. Gradually enable sidecar injection in staging and validate behaviour.
2. Promote to production via canary releases; monitor metrics and tracing.
3. If SLOs regress, disable injection with
   `kubectl label namespace <ns> istio-injection-` and run
   `istioctl uninstall --purge` to remove the control plane.
4. Revert affected deployments following the steps in
   [rollback_plan.md](rollback_plan.md).

