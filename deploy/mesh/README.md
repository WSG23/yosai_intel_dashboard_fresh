# Service Mesh Sandbox

Prototype manifests for evaluating service-to-service authorization in a sandbox
cluster. Two variants are provided:

* **Istio** – `istio-policy.yaml` uses an `AuthorizationPolicy` allowing the
  `frontend` service account to call the `backend` service with GET and POST.
* **Linkerd** – `linkerd-policy.yaml` uses a `ServerAuthorization` that grants
  the same access via Linkerd's policy APIs.

Apply the appropriate manifest after installing the mesh:

```bash
kubectl apply -f deploy/mesh/istio-policy.yaml    # for Istio
kubectl apply -f deploy/mesh/linkerd-policy.yaml  # for Linkerd
```

These examples are intended for experimentation and should be adapted before
production use.
