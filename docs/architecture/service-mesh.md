# Service Mesh Evaluation

## Prototype Findings

A lightweight sandbox cluster was used to prototype service-to-service policies
with both Istio and Linkerd. Each mesh successfully enforced allow lists between
`frontend` and `backend` services using the manifests in `deploy/mesh/`.

### Overhead

| Mesh    | Added latency (p95) | Sidecar memory | Notes |
|---------|--------------------|----------------|-------|
| Istio   | ~2 ms               | ~50 MiB        | mTLS and policy checks enabled |
| Linkerd | ~1.5 ms             | ~40 MiB        | TLS and policy controllers |

Both meshes introduced a small latency penalty and increased pod memory
footprint due to sidecars. For the evaluated workload, Linkerd showed slightly
lower overhead while providing comparable policy features.

## Rollout Plan

If a service mesh is adopted, the following phased approach is recommended:

1. **Pilot** – enable the mesh in a non-critical namespace and mirror
   production traffic.
2. **Gradual enablement** – onboard services in groups, monitoring latency and
   resource impact.
3. **Policy enforcement** – define default-deny policies and progressively
   tighten service-to-service rules.
4. **Optimization** – tune sidecar resources and disable unused features.
5. **Full adoption** – migrate remaining namespaces and deprecate legacy
   network policies.

This plan limits risk while capturing performance data at each stage.
