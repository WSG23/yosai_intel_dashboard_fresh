#!/usr/bin/env bash
set -euo pipefail

# Install k3s (lightweight Kubernetes)
if ! command -v k3s >/dev/null 2>&1; then
  curl -sfL https://get.k3s.io | sh -
fi

export KUBECONFIG=/etc/rancher/k3s/k3s.yaml

# Install Istio CLI if missing
if ! command -v istioctl >/dev/null 2>&1; then
  curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.21.0 sh -
  export PATH=$PATH:$(pwd)/istio-1.21.0/bin
fi

# Install Istio control plane using the demo profile
istioctl install -y --set profile=demo

# Label namespaces for automatic sidecar injection
for ns in yosai-prod yosai-staging yosai-dev; do
  kubectl label namespace "$ns" istio-injection=enabled --overwrite
done

# Install Strimzi Kafka operator
kubectl create namespace kafka --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f https://strimzi.io/install/latest?namespace=kafka -n kafka

# Install observability stack (Prometheus and Grafana via Helm)
if ! command -v helm >/dev/null 2>&1; then
  curl https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3 | bash
fi
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace

# Create application namespaces
for ns in yosai-prod yosai-staging yosai-dev; do
  kubectl create namespace "$ns" --dry-run=client -o yaml | kubectl apply -f -
done

# Apply base manifests
kubectl apply -f k8s/base

# Apply Istio service mesh configuration
kubectl apply -f k8s/istio

