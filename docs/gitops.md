# GitOps with ArgoCD

This repository uses a GitOps workflow powered by [ArgoCD](https://argo-cd.readthedocs.io/).
Kubernetes manifests and Helm values are stored in the repository and
synchronized to the cluster by ArgoCD.

## Repository Structure

```
argocd/
  applications/   # ArgoCD Application CRDs
environments/
  dev/            # Environment specific Helm values
  staging/
  prod/
helm/
  yosai-intel/    # Helm chart for the dashboard
```

Each environment has an `Application` definition in `argocd/applications/`
which references the common Helm chart and the environment specific values
file under `environments/<env>/values.yaml`.

## RBAC

ArgoCD runs in the `argocd` namespace. Application resources are created in
namespaces specific to each environment (`yosai-dev`, `yosai-staging`, and
`yosai-prod`). Access to modify the GitOps directories is restricted to
operators with write access to the repository.

## Sync Policies

Applications use automated sync with self-healing enabled:

```
syncPolicy:
  automated:
    prune: true
    selfHeal: true
```

This ensures ArgoCD continuously reconciles the desired state from Git with
the cluster. Changes merged into `main` are automatically picked up by the
running ArgoCD instance and applied to the target namespaces.
