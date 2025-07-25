# Kubernetes Development Environment

This guide explains how to start a local Kubernetes cluster for the Yōsai Intel Dashboard.
It installs [k3s](https://k3s.io), [Istio](https://istio.io), the [Strimzi](https://strimzi.io) Kafka operator, and a small observability stack.

## Setup

Run the helper script which installs all dependencies and creates the required namespaces:

```bash
scripts/setup_k8s_dev.sh
```

The script installs k3s if it is not already present, then deploys Istio, the Strimzi operator, and Prometheus/Grafana via Helm.

It also applies the manifests in `k8s/istio` so the service mesh is deployed automatically.

## Deploying the Dashboard

After the cluster is ready apply the base manifests and the production manifests:

```bash
kubectl apply -f k8s/base
kubectl apply -f k8s/production
```

The application will be available on the Node IP at port `80` once the pods become ready.
